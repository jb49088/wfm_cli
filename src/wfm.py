# ================================================================================
# =                                     WFM                                      =
# ================================================================================

# TODO: implement status changing
# TODO: implement copying, deleting, going to sellers listings

import json
import shlex
from pathlib import Path
from typing import Any

import requests
from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.history import FileHistory

from config import BROWSER_HEADERS
from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings
from utils import clear_screen

APP_DIR = Path.home() / ".wfm"
COOKIES_FILE = APP_DIR / "cookies.json"
HISTORY_FILE = APP_DIR / "history"


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


def build_authenticated_headers(cookies: dict[str, str]) -> dict[str, str]:
    """Build authenticated headers with cookies."""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://warframe.market/",
        "language": "en",
        "platform": "pc",
        "crossplay": "true",
        "Origin": "https://warframe.market",
        "Cookie": f"JWT={cookies['jwt']}; cf_clearance={cookies['cf']}",
    }

    headers.update(BROWSER_HEADERS)

    return headers


def get_user_info(headers: dict[str, str]) -> dict[str, Any]:
    """Get the authenticated users profile info."""
    r = requests.get(url="https://api.warframe.market/v2/me", headers=headers)
    r.raise_for_status()

    data = r.json()["data"]

    return {
        "ingameName": data.get("ingameName", "Unknown"),
        "slug": data["slug"],
        "reputation": data.get("reputation", 0),
        "platform": data["platform"],
        "crossplay": data.get("crossplay", False),
    }


def get_all_items() -> list[dict[str, Any]]:
    """Extract all raw item data."""
    r = requests.get(
        url="https://api.warframe.market/v2/items", headers=BROWSER_HEADERS
    )
    r.raise_for_status()

    return r.json()["data"]


def build_id_to_name_mapping(all_items: list[dict[str, Any]]) -> dict[str, str]:
    return {item["id"]: item["i18n"]["en"]["name"] for item in all_items}


def build_name_to_max_rank_mapping(
    all_items: list[dict[str, Any]], id_to_name: dict[str, str]
) -> dict[str, int | None]:
    return {id_to_name[item["id"]]: item.get("maxRank") for item in all_items}


def handle_search(args: list[str]) -> tuple[str, dict[str, Any]]:
    """Parse arguments for the search functionality."""
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


def handle_listings(args: list[str]) -> dict[str, Any]:
    """Parse arguments for displaying the currently authenticated user's listings."""
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
    print("  profile")
    print("      Display your account information")
    print()
    print("  help")
    print("      Show this help message")
    print()


def wfm() -> None:
    """Main entry point for wfm."""
    ensure_app_dir()

    if not COOKIES_FILE.exists():
        cookies = prompt_for_cookies()
        ensure_cookies_file(cookies)

    cookies = load_cookies()
    authenticated_headers = build_authenticated_headers(cookies)
    user_info = get_user_info(authenticated_headers)

    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    max_ranks = build_name_to_max_rank_mapping(all_items, id_to_name)

    session = PromptSession(history=FileHistory(HISTORY_FILE))

    status = "\033[32mIn Game\033[0m"

    while True:
        try:
            cmd = session.prompt(ANSI(f"wfm [{status}]> ")).strip()
        except KeyboardInterrupt:
            break

        parts = shlex.split(cmd)
        action = parts[0].lower()
        args = parts[1:]

        if action == "search":
            item, kwargs = handle_search(args)
            display_item_listings(id_to_name, max_ranks, item, **kwargs)

        elif action == "listings":
            kwargs = handle_listings(args)
            display_user_listings(id_to_name, max_ranks, user_info["slug"], **kwargs)

        elif action == "profile":
            display_profile(user_info)

        elif action == "help":
            display_help()

        elif action == "clear":
            clear_screen()

        elif action == "exit" or action == "quit":
            break

        else:
            print(f"Unknown command: '{action}'. Use 'help' to see available commands.")


if __name__ == "__main__":
    wfm()
