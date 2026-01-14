# ================================================================================
# =                                   WFM_CLI                                    =
# ================================================================================

# TODO: cache full item list on start to reduce requests
# TODO: implement status changing
# TODO: implement my listings
# TODO: finish basic argument parsing functionality

import shlex

from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.history import FileHistory

from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings
from utils import clear_screen


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


def wfm_cli():
    """Main entry point for wfm_cli."""
    session = PromptSession(history=FileHistory("data/history"))
    status = "\033[32mIn Game\033[0m"
    while True:
        try:
            cmd = session.prompt(ANSI(f"wfm_cli [{status}]> ")).strip()
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
        wfm_cli()
    except KeyboardInterrupt:
        pass
