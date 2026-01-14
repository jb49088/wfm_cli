# ================================================================================
# =                                     WFM                                      =
# ================================================================================

# TODO: cache full item list on start to reduce requests
# TODO: implement status changing
# TODO: implement my listings
# TODO: finish basic argument parsing functionality

import shlex
from pathlib import Path

from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.history import FileHistory

from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings
from utils import clear_screen

APP_DIR = Path.home() / ".wfm"
CONFIG_FILE = APP_DIR / "config.json"
HISTORY_FILE = APP_DIR / "history"


def ensure_app_dir():
    APP_DIR.mkdir(exist_ok=True)


def handle_search(args):
    """Parse and display an items listings."""
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

    display_item_listings(item=item, **kwargs)


def wfm():
    """Main entry point for wfm."""
    ensure_app_dir()
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
            handle_search(args)

        elif action == "clear":
            clear_screen()


if __name__ == "__main__":
    try:
        wfm()
    except KeyboardInterrupt:
        pass
