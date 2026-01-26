# ================================================================================
# =                                     WFM                                      =
# ================================================================================

# TODO: implement cookies checking
# TODO: implement project-wide error handling

import asyncio
import json
import shlex
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
from config import HISTORY_FILE
from display import DEFAULT_ORDERS, clear_screen, display_help, display_profile
from filters import sort_listings
from parsers import (
    parse_add_args,
    parse_edit_args,
    parse_listings_args,
    parse_search_args,
    parse_seller_args,
)
from websocket import open_websocket

STATUS_MAPPING = {
    "invisible": "\033[2mInvisible\033[0m",  # Grey
    "online": "\033[34mOnline\033[0m",  # Blue
    "ingame": "\033[32mIn Game\033[0m",  # Green
}


def build_id_to_name_mapping(all_items: list[dict[str, Any]]) -> dict[str, str]:
    return {item["id"]: item["i18n"]["en"]["name"] for item in all_items}


def build_id_to_tags_mapping(all_items: list[dict[str, Any]]) -> dict[str, set[str]]:
    return {item["id"]: set(item["tags"]) for item in all_items}


def build_id_to_bulkTradable_mapping(
    all_items: list[dict[str, Any]],
) -> dict[str, bool]:
    return {item["id"]: item.get("bulkTradable", False) for item in all_items}


def build_name_to_max_rank_mapping(
    all_items: list[dict[str, Any]], id_to_name: dict[str, str]
) -> dict[str, int | None]:
    return {id_to_name[item["id"]]: item.get("maxRank") for item in all_items}


def build_name_to_slug_mapping(all_items: list[dict[str, Any]]) -> dict[str, str]:
    return {item["i18n"]["en"]["name"].lower(): item["slug"] for item in all_items}


async def wfm() -> None:
    """Main entry point and top-level orchestration function for wfm."""
    ensure_app_dir()

    if not COOKIES_FILE.exists():
        cookies = prompt_for_cookies()
        ensure_cookies_file(cookies)

    cookies = load_cookies()
    cookie_header = build_cookie_header(cookies)
    authenticated_headers = build_authenticated_headers(cookie_header)

    async with aiohttp.ClientSession() as session:
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

        user_info, all_items = await asyncio.gather(
            get_user_info(session, authenticated_headers),
            get_all_items(session),
        )

        await initial_status_event.wait()

        id_to_name = build_id_to_name_mapping(all_items)
        id_to_tags = build_id_to_tags_mapping(all_items)
        id_to_bulkTradable = build_id_to_bulkTradable_mapping(all_items)
        name_to_max_rank = build_name_to_max_rank_mapping(all_items, id_to_name)
        name_to_id = {v.lower(): k for k, v in id_to_name.items()}
        name_to_slug = build_name_to_slug_mapping(all_items)

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
                if args[0].isdigit() and current_listings:
                    listing_index = int(args[0]) - 1
                    if 0 <= listing_index < len(current_listings):
                        _, kwargs = parse_search_args(args)
                        item_name = current_listings[listing_index]["item"]
                        item_slug = name_to_slug[item_name.lower()]
                    else:
                        print(
                            f"\nInvalid listing number. Valid range: 1-{len(current_listings)}\n"
                        )
                        continue
                else:
                    item, kwargs = parse_search_args(args)
                    item_slug = name_to_slug[item.lower()]

                current_listings = await search(
                    item_slug, id_to_name, name_to_max_rank, session, **kwargs
                )

            elif action == "listings":
                kwargs = parse_listings_args(args)
                current_listings = await listings(
                    id_to_name,
                    name_to_max_rank,
                    user_info["slug"],
                    authenticated_headers,
                    session,
                    **kwargs,
                )

            elif action == "seller":
                kwargs = parse_seller_args(args)
                seller_num = int(args[0]) - 1
                seller_slug = current_listings[seller_num]["slug"]
                seller_name = current_listings[seller_num]["seller"]
                current_listings = await seller(
                    id_to_name,
                    name_to_max_rank,
                    seller_slug,
                    seller_name,
                    session,
                    **kwargs,
                )

            elif action == "add":
                kwargs = parse_add_args(args, name_to_id)
                await add_listing(
                    session,
                    authenticated_headers,
                    id_to_tags,
                    id_to_bulkTradable,
                    **kwargs,
                )
                print("\nListing added.\n")

            elif action == "show":
                if args[0] == "all":
                    await change_all_visibility(session, True, authenticated_headers)
                    print("\nAll listings are now visible.\n")
                else:
                    listing_id = current_listings[int(args[0]) - 1]["id"]
                    await change_visibility(
                        session, listing_id, True, authenticated_headers
                    )
                    print(f"\nListing {args[0]} is now visible.\n")

            elif action == "hide":
                if args[0] == "all":
                    await change_all_visibility(session, False, authenticated_headers)
                    print("\nAll listings are now hidden.\n")
                else:
                    listing_id = current_listings[int(args[0]) - 1]["id"]
                    await change_visibility(
                        session, listing_id, False, authenticated_headers
                    )
                    print(f"\nListing {args[0]} is now hidden.\n")

            elif action == "delete":
                listing_id = current_listings[int(args[0]) - 1]["id"]
                await delete_listing(session, listing_id, authenticated_headers)
                print(f"\nDeleted listing {args[0]}.\n")

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
                print(f"\nListing {args[0]} updated.\n")

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
                    print(f"Bumped listing {args[0]}.")

                print()

            elif action == "copy":
                listing_to_copy = current_listings[int(args[0]) - 1]
                copy(listing_to_copy, name_to_max_rank)

            elif action == "links":
                await links(
                    all_items,
                    id_to_name,
                    user_info["slug"],
                    authenticated_headers,
                    session,
                    prompt_session,
                )

            elif action == "status":
                message = {
                    "route": "@wfm|cmd/status/set",
                    "payload": {"status": args[0], "duration": None},
                }
                status_response_event = asyncio.Event()
                await status_queue.put((json.dumps(message), status_response_event))
                await status_response_event.wait()

            elif action == "sync":
                await sync(
                    id_to_name,
                    id_to_tags,
                    id_to_bulkTradable,
                    user_info["slug"],
                    session,
                    authenticated_headers,
                )

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
                print(
                    f"\nUnknown command: '{action}'. Use 'help' to see available commands.\n"
                )


if __name__ == "__main__":
    asyncio.run(wfm())
