# ================================================================================
# =                                     WFM                                      =
# ================================================================================

# TODO: implement project-wide error handling

import asyncio
import json
import shlex
import sys
from typing import Any

import aiohttp
from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.history import FileHistory

from api import (
    add_listing,
    change_all_visibility,
    change_visibility,
    delete_listing,
    edit_listing,
    extract_user_listings,
    get_all_items,
    get_user_info,
)
from auth import (
    COOKIES_FILE,
    build_authenticated_headers,
    build_cookie_header,
    ensure_app_dir,
    ensure_cookies_file,
    load_cookies,
    prompt_for_cookies,
)
from commands import copy, links, listings, search, seller, sync
from config import APP_DIR, HISTORY_FILE
from display import DEFAULT_ORDERS, clear_screen, display_help, display_profile
from filters import sort_listings
from parsers import (
    parse_add_args,
    parse_edit_args,
    parse_listings_args,
    parse_search_args,
    parse_seller_args,
)
from validators import validate_add_args, validate_seller_listing_selection
from websocket import open_websocket

STATUS_MAPPING = {
    "ingame": "\033[32mIn Game\033[0m",  # Green
    "online": "\033[34mOnline\033[0m",  # Blue
    "invisible": "\033[2mInvisible\033[0m",  # Grey
}


def build_id_to_name_mapping(all_items: list[dict[str, Any]]) -> dict[str, str]:
    return {item["id"]: item["i18n"]["en"]["name"] for item in all_items}


def build_id_to_tags_mapping(all_items: list[dict[str, Any]]) -> dict[str, set[str]]:
    return {item["id"]: set(item["tags"]) for item in all_items}


def build_id_to_bulkTradable_mapping(
    all_items: list[dict[str, Any]],
) -> dict[str, bool]:
    return {item["id"]: item.get("bulkTradable", False) for item in all_items}


def build_id_to_max_rank_mapping(
    all_items: list[dict[str, Any]],
) -> dict[str, int | None]:
    return {item["id"]: item.get("maxRank") for item in all_items}


def build_id_to_slug_mapping(
    all_items: list[dict[str, Any]],
) -> dict[str, str]:
    return {item["id"]: item["slug"] for item in all_items}


async def wfm() -> None:
    """Main entry point and top-level orchestration function for wfm."""
    if not APP_DIR.exists():
        print(
            "Welcome to wfm.\n"
            "\nTo get started, enter your browser cookies.\n"
            "\nSee the README for instructions: https://github.com/jb49088/wfm/blob/master/README.md\n"
        )
        ensure_app_dir()
        cookies = await prompt_for_cookies()
        print()
        ensure_cookies_file(cookies)

    if not COOKIES_FILE.exists():
        print("Cookies file not detected.\n")
        cookies = await prompt_for_cookies()
        print()
        ensure_cookies_file(cookies)

    cookies = load_cookies()

    async with aiohttp.ClientSession() as session:
        for attempt in range(4):
            cookie_header = build_cookie_header(cookies)
            authenticated_headers = build_authenticated_headers(cookie_header)

            initial_status_event = asyncio.Event()
            status_queue = asyncio.Queue()
            status_state = {"status": "invisible"}

            websocket_task = asyncio.create_task(
                open_websocket(
                    cookie_header,
                    status_state,
                    initial_status_event,
                    status_queue,
                )
            )

            try:
                user_info, all_items = await asyncio.gather(
                    get_user_info(session, authenticated_headers),
                    get_all_items(session),
                )

                await initial_status_event.wait()
                break  # Success

            except aiohttp.ClientResponseError:
                websocket_task.cancel()

                if attempt == 3:
                    print("Too many failed attempts. Exiting.")
                    sys.exit()

                print("Authentication failed.\n")
                cookies = await prompt_for_cookies()
                print()
                ensure_cookies_file(cookies)

        id_to_name = build_id_to_name_mapping(all_items)
        id_to_tags = build_id_to_tags_mapping(all_items)
        id_to_bulkTradable = build_id_to_bulkTradable_mapping(all_items)
        id_to_max_rank = build_id_to_max_rank_mapping(all_items)
        id_to_slug = build_id_to_slug_mapping(all_items)

        name_to_id = {v.lower(): k for k, v in id_to_name.items()}

        prompt_session = PromptSession(history=FileHistory(HISTORY_FILE))

        current_listings = []

        while True:
            try:
                cmd = await prompt_session.prompt_async(
                    ANSI(f"wfm [{STATUS_MAPPING[status_state['status']]}]> ")
                )
            except (KeyboardInterrupt, EOFError):
                websocket_task.cancel()
                break

            parts = shlex.split(cmd)
            action = parts[0].lower()
            args = parts[1:]

            if action == "search":
                if not args:
                    print("\nNo item specified.\n")
                    continue
                if args[0].isdigit():
                    if current_listings:
                        listing_index = int(args[0]) - 1
                        if 0 <= listing_index < len(current_listings):
                            _, kwargs = parse_search_args(args)
                            item_id = current_listings[listing_index]["itemId"]
                            item_slug = id_to_slug[item_id]
                        else:
                            print("\nInvalid listing number.\n")
                            continue
                    else:
                        print("\nNo listings available.\n")
                        continue
                else:
                    item, kwargs = parse_search_args(args)
                    if item.lower() not in name_to_id:
                        print(f"\nItem '{item}' not found.\n")
                        continue
                    item_id = name_to_id[item]
                    item_slug = id_to_slug[item_id]

                current_listings = await search(
                    item_slug, id_to_name, id_to_max_rank, session, **kwargs
                )

            elif action == "listings":
                kwargs = parse_listings_args(args)

                success, error, current_listings = await listings(
                    id_to_name,
                    id_to_max_rank,
                    user_info["slug"],
                    authenticated_headers,
                    session,
                    **kwargs,
                )

                if not success:
                    print(f"\n{error}\n")

            elif action == "seller":
                success, error, listing = validate_seller_listing_selection(
                    args, current_listings
                )

                if not success:
                    print(f"\n{error}\n")
                    continue

                assert listing is not None

                kwargs = parse_seller_args(args)

                seller_slug = listing["slug"]
                seller_name = listing["seller"]

                current_listings = await seller(
                    id_to_name,
                    id_to_max_rank,
                    seller_slug,
                    seller_name,
                    session,
                    **kwargs,
                )

            elif action == "add":
                kwargs = parse_add_args(args)

                success, error = validate_add_args(
                    kwargs,
                    name_to_id,
                    id_to_name,
                    id_to_max_rank,
                    id_to_tags,
                    id_to_bulkTradable,
                )

                if not success:
                    print(f"\n{error}\n")
                    continue

                await add_listing(session, authenticated_headers, **kwargs)

                item_name = id_to_name[kwargs["item_id"]]
                print(f"\n{item_name} listing added.\n")

            elif action == "show":
                if args[0] == "all":
                    await change_all_visibility(session, True, authenticated_headers)
                    print("\nAll listings visible.\n")
                else:
                    listing = current_listings[int(args[0]) - 1]
                    listing_id = listing["id"]
                    item = listing["item"]
                    await change_visibility(
                        session, listing_id, True, authenticated_headers
                    )
                    print(f"\n{item} listing visible.\n")

            elif action == "hide":
                if args[0] == "all":
                    await change_all_visibility(session, False, authenticated_headers)
                    print("\nAll listings hidden.\n")
                else:
                    listing = current_listings[int(args[0]) - 1]
                    listing_id = listing["id"]
                    item = listing["item"]
                    await change_visibility(
                        session, listing_id, False, authenticated_headers
                    )
                    print(f"\n{args[0]} listing hidden.\n")

            elif action == "delete":
                listing = current_listings[int(args[0]) - 1]
                listing_id = listing["id"]
                item = listing["item"]
                await delete_listing(session, listing_id, authenticated_headers)
                print(f"\nDeleted {item} listing.\n")

            elif action == "edit":
                listing = current_listings[int(args[0]) - 1]
                kwargs = parse_edit_args(args, listing)
                await edit_listing(
                    session,
                    authenticated_headers,
                    listing["id"],
                    listing["itemId"],
                    id_to_tags,
                    id_to_bulkTradable,
                    **kwargs,
                )
                print(f"\nUpdated {listing['item']} listing.\n")

            elif action == "bump":
                if args[0] == "all":
                    print("\nBumping all listings...\n")
                    user_listings = await extract_user_listings(
                        session, user_info["slug"], id_to_name, authenticated_headers
                    )
                    sorted_listings, _ = sort_listings(
                        user_listings, "updated", "asc", DEFAULT_ORDERS
                    )
                    for listing in sorted_listings:
                        await edit_listing(
                            session,
                            authenticated_headers,
                            listing["id"],
                            listing["itemId"],
                            id_to_tags,
                            id_to_bulkTradable,
                            listing["price"],
                            listing["quantity"],
                            listing["rank"],
                            listing["visible"],
                        )
                        print(f"Bumped {listing['item']} listing.")
                        await asyncio.sleep(0.5)  # Rate limit
                else:
                    listing = current_listings[int(args[0]) - 1]
                    await edit_listing(
                        session,
                        authenticated_headers,
                        listing["id"],
                        listing["itemId"],
                        id_to_tags,
                        id_to_bulkTradable,
                        listing["price"],
                        listing["quantity"],
                        listing["rank"],
                        listing["visible"],
                    )
                    print(f"\nBumped {listing['item']} listing.")

                print()

            elif action == "copy":
                if not args or not args[0].isdigit():
                    print("\nNo listing specified.\n")
                    continue
                if not current_listings:
                    print("\nNo listings available.\n")
                    continue
                listing_index = int(args[0]) - 1
                if not (0 <= listing_index < len(current_listings)):
                    print("\nInvalid listing number.\n")
                    continue
                if "id" in current_listings[listing_index]:
                    print("\nCannot copy own listings.\n")
                    continue
                listing_to_copy = current_listings[listing_index]
                error = copy(listing_to_copy, id_to_max_rank)
                print(f"\nCopied to clipboard: {error}\n")

            elif action == "links":
                success, error = await links(
                    all_items,
                    id_to_name,
                    user_info["slug"],
                    authenticated_headers,
                    session,
                    prompt_session,
                )

                if not success:
                    print(f"\n{error}\n")

            elif action == "status":
                if not args:
                    print("\nNo status specified.\n")
                    continue

                if args[0] not in STATUS_MAPPING:
                    print(f"\n'{args[0]}' is not a valid status.\n")
                    continue

                error = {
                    "route": "@wfm|cmd/status/set",
                    "payload": {"status": args[0], "duration": None},
                }
                status_response_event = asyncio.Event()
                await status_queue.put((json.dumps(error), status_response_event))
                await status_response_event.wait()

            elif action == "sync":
                success, error = await sync(
                    id_to_name,
                    id_to_tags,
                    id_to_bulkTradable,
                    user_info["slug"],
                    session,
                    authenticated_headers,
                )

                if not success:
                    print(f"\n{error}\n")

            elif action == "profile":
                user_info = await get_user_info(session, authenticated_headers)
                display_profile(user_info)

            elif action == "clear":
                clear_screen()

            elif action == "help":
                display_help()

            elif action == "exit" or action == "quit":
                break

            else:
                print(f"\n'{action}' is not a valid command. See 'help'.\n")


if __name__ == "__main__":
    asyncio.run(wfm())
