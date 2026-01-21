# ================================================================================
# =                                     WFM                                      =
# ================================================================================

# TODO: implemnt sync feature
# TODO: implement cookies checking
# TODO: implement project-wide error handling

import asyncio
import json
import shlex
from pathlib import Path
from typing import Any

import aiohttp
import pyperclip
import websockets
from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.history import FileHistory

from config import USER_AGENT
from links import links
from listings import listings
from search import search
from seller import seller
from utils import build_authenticated_headers, build_cookie_header, clear_screen

APP_DIR = Path.home() / ".wfm"
COOKIES_FILE = APP_DIR / "cookies.json"
HISTORY_FILE = APP_DIR / "history"

WS_URI = "wss://ws.warframe.market/socket"
AUTH_MESSAGE = '{"route":"@wfm|cmd/auth/signIn","payload":{"token":""}}'

STATUS_MAPPING = {
    "invisible": "\033[31mInvisible\033[0m",  # Red
    "online": "\033[34mOnline\033[0m",  # Blue
    "ingame": "\033[32mIn Game\033[0m",  # Green
}


def ensure_app_dir() -> None:
    """Make sure the application data directory exists."""
    APP_DIR.mkdir(exist_ok=True)


def prompt_for_cookies() -> dict[str, str]:
    """Prompt user for JWT token and CF clearance."""
    cookies = {
        "jwt": input("Enter your JWT token: "),
        "cf": input("Enter your CF clearance: "),
    }

    return cookies


def ensure_cookies_file(cookies: dict[str, str]) -> None:
    """Make sure the config file exists."""
    with COOKIES_FILE.open("w") as f:
        json.dump(cookies, f)


def load_cookies() -> dict[str, str]:
    """Load cookies from the config file."""
    with COOKIES_FILE.open() as f:
        return json.load(f)


async def get_user_info(
    session: aiohttp.ClientSession, headers: dict[str, str]
) -> dict[str, Any]:
    """Get the authenticated users profile info."""
    async with session.get(
        url="https://api.warframe.market/v2/me", headers=headers
    ) as r:
        r.raise_for_status()
        data = (await r.json())["data"]

        return {
            "ingameName": data.get("ingameName", "Unknown"),
            "slug": data["slug"],
            "reputation": data.get("reputation", 0),
            "platform": data["platform"],
            "crossplay": data.get("crossplay", False),
        }


async def get_all_items(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    """Extract all raw item data."""
    async with session.get(
        url="https://api.warframe.market/v2/items", headers=USER_AGENT
    ) as r:
        r.raise_for_status()

        return (await r.json())["data"]


def build_id_to_name_mapping(all_items: list[dict[str, Any]]) -> dict[str, str]:
    return {item["id"]: item["i18n"]["en"]["name"] for item in all_items}


def build_name_to_max_rank_mapping(
    all_items: list[dict[str, Any]], id_to_name: dict[str, str]
) -> dict[str, int | None]:
    return {id_to_name[item["id"]]: item.get("maxRank") for item in all_items}


def build_name_to_slug_mapping(all_items: list[dict[str, Any]]) -> dict[str, str]:
    return {item["i18n"]["en"]["name"].lower(): item["slug"] for item in all_items}


def parse_search_args(args: list[str]) -> tuple[str, dict[str, Any]]:
    item = args[0]

    kwargs = {
        "sort": "price",
        "order": None,
        "rank": None,
        "status": "ingame",
    }

    rest = args[1:]
    pairs = zip(rest[::2], rest[1::2])

    for key, value in pairs:
        kwargs[key] = value

    if kwargs["rank"]:
        kwargs["rank"] = int(kwargs["rank"])

    return item, kwargs


def parse_listings_args(args: list[str]) -> dict[str, Any]:
    kwargs = {
        "sort": "updated",
        "order": None,
        "rank": None,
    }

    pairs = zip(args[::2], args[1::2])

    for key, value in pairs:
        kwargs[key] = value

    if kwargs["rank"]:
        kwargs["rank"] = int(kwargs["rank"])

    return kwargs


def parse_add_args(args: list[str], name_to_id: dict[str, str]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"item_id": name_to_id[args[0]]}

    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        kwargs[key] = int(value)

    return kwargs


def parse_seller_args(args: list[str]) -> dict[str, Any]:
    kwargs = {
        "sort": "updated",
        "order": None,
        "rank": None,
    }

    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        kwargs[key] = value

    if kwargs["rank"]:
        kwargs["rank"] = int(kwargs["rank"])

    return kwargs


def parse_edit_args(args: list[str], listing: dict[str, Any]) -> dict[str, Any]:
    kwargs = {
        "price": listing["price"],
        "quantity": listing["quantity"],
        "rank": listing["rank"],
        "visible": listing["visible"],
    }

    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        if key != "visible":
            value = int(value)
        kwargs[key] = value

    return kwargs


async def add_listing(
    session: aiohttp.ClientSession,
    headers: dict[str, str],
    item_id: str,
    price: int,
    quantity: int,
    rank=None,
) -> None:
    payload = {
        "itemId": item_id,
        "platinum": price,
        "quantity": quantity,
        "type": "sell",
        "visible": True,
    }
    if rank is not None:
        payload["rank"] = rank

    async with session.post(
        "https://api.warframe.market/v2/order", json=payload, headers=headers
    ) as r:
        r.raise_for_status()


async def change_visibility(
    session: aiohttp.ClientSession,
    listing_id: str,
    visibility: bool,
    headers: dict[str, str],
) -> None:
    async with session.patch(
        url=f"https://api.warframe.market/v2/order/{listing_id}",
        json={"visible": visibility},
        headers=headers,
    ) as r:
        r.raise_for_status()


async def change_all_visibility(
    session: aiohttp.ClientSession, visibility: bool, headers: dict[str, str]
) -> None:
    async with session.patch(
        url="https://api.warframe.market/v2/orders/group/all",
        json={"type": "sell", "visible": visibility},
        headers=headers,
    ) as r:
        r.raise_for_status()


async def delete_listing(
    session: aiohttp.ClientSession, listing_id: str, headers: dict[str, str]
) -> None:
    async with session.delete(
        url=f"https://api.warframe.market/v2/order/{listing_id}",
        headers=headers,
    ) as r:
        r.raise_for_status()


async def edit_listing(
    session: aiohttp.ClientSession,
    listing_id: str,
    headers: dict[str, str],
    price: int,
    quantity: int,
    rank: int,
    visible: bool,
) -> None:
    async with session.patch(
        url=f"https://api.warframe.market/v2/order/{listing_id}",
        headers=headers,
        json={
            "platinum": price,
            "quantity": quantity,
            "rank": rank,
            "visible": visible,
        },
    ) as r:
        r.raise_for_status()


def copy(listing_to_copy: dict[str, Any], max_ranks: dict[str, int | None]) -> None:
    """Copy a listing for in-game whispering."""
    item_name = listing_to_copy["item"]

    if listing_to_copy.get("rank") is not None:
        item_name = (
            f"{item_name} (rank {listing_to_copy['rank']}/{max_ranks[item_name]})"
        )

    segments = [
        "WTB",
        item_name,
        f"{listing_to_copy['price']}p",
    ]
    message = f"/w {listing_to_copy['seller']} {' | '.join(segments)}"

    pyperclip.copy(message)

    print(f"\nCopied to clipboard: {message}\n")


def display_profile(user_info: dict[str, Any]) -> None:
    """Display basic profile info for the authenticated user."""
    platform_mapping = {
        "pc": "PC",
        "ps4": "PS4",
        "xbox": "Xbox",
        "switch": "Nintendo Switch",
        "mobile": "Mobile",
    }
    print()
    print(f"Username:   {user_info['ingameName']}")
    print(f"Reputation: {user_info['reputation']}")
    print(f"Platform:   {platform_mapping[user_info['platform']]}")
    print(f"Crossplay:  {'Enabled' if user_info['crossplay'] else 'Disabled'}")
    print()


def display_help() -> None:
    """Display all commands and example usage."""
    print()
    print("Available commands:")
    print(
        "  search <item> [sort <field>] [order <asc|desc>] [rank <number>] [status <all|ingame|online|offline>]"
    )
    print("      Search for item listings (all filters optional)")
    print('      Example: search "ammo drum"')
    print('      Example: search "ammo drum" rank 5 sort reputation')
    print("      Example: search serration rank 0 status ingame")
    print()
    print("  listings [sort <field>] [order <asc|desc>] [rank <number>]")
    print("      Display your active listings (all filters optional)")
    print("      Example: listings")
    print("      Example: listings sort price")
    print("      Example: listings rank 0 sort updated order desc")
    print()
    print("  copy <number>")
    print("      Copy a listing whisper message to clipboard")
    print("      Example: copy 3")
    print()
    print("  profile")
    print("      Display your account information")
    print()
    print("  clear")
    print("      Clear the screen")
    print()
    print("  help")
    print("      Show this help message")
    print()
    print("  exit, quit")
    print("      Exit the program")
    print()


async def open_websocket(
    cookie_header: dict[str, str],
    state: dict[str, str],
    initial_status_event: asyncio.Event,
    status_queue: asyncio.Queue,
) -> None:
    """Connect to WebSocket, authenticate, and manage status updates."""
    async with websockets.connect(
        uri=WS_URI,
        additional_headers=cookie_header,
    ) as ws:
        await ws.send(AUTH_MESSAGE)

        current_response_event = None

        async def send_status_updates():
            """Send status updates from the queue to the WebSocket."""
            nonlocal current_response_event

            while True:
                status_message, response_event = await status_queue.get()
                await ws.send(status_message)
                current_response_event = response_event

        async def receive_messages():
            nonlocal current_response_event

            while True:
                message = json.loads(await ws.recv())
                payload_status = message.get("payload", {}).get("status")

                if payload_status:
                    state["status"] = payload_status
                    initial_status_event.set()

                    if current_response_event:
                        current_response_event.set()
                        current_response_event = None

        await asyncio.gather(receive_messages(), send_status_updates())


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
        state = {}

        websocket_task = asyncio.create_task(
            open_websocket(
                cookie_header,
                state,
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
        name_to_max_rank = build_name_to_max_rank_mapping(all_items, id_to_name)

        name_to_id = {v.lower(): k for k, v in id_to_name.items()}
        name_to_slug = build_name_to_slug_mapping(all_items)

        prompt_session = PromptSession(history=FileHistory(HISTORY_FILE))

        while True:
            try:
                cmd = await prompt_session.prompt_async(
                    ANSI(f"wfm [{STATUS_MAPPING[state['status']]}]> ")
                )
            except (KeyboardInterrupt, EOFError):
                websocket_task.cancel()
                break

            parts = shlex.split(cmd)
            action = parts[0].lower()
            args = parts[1:]

            if action == "search":
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
                await add_listing(session, authenticated_headers, **kwargs)
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
                listing_id = current_listings[int(args[0]) - 1]["id"]
                listing_to_edit = current_listings[int(args[0]) - 1]
                kwargs = parse_edit_args(args, listing_to_edit)
                await edit_listing(session, listing_id, authenticated_headers, **kwargs)
                print(f"\nListing {args[0]} updated.\n")

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

            elif action == "profile":
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
