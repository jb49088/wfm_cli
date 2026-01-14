# ================================================================================
# =                                   WFM_CLI                                    =
# ================================================================================

from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings
from utils import clear_screen


def wfm_cli():
    while True:
        try:
            cmd = input("wfm_cli> ").strip()
        except KeyboardInterrupt:
            break

        parts = cmd.split()
        action = parts[0].lower()
        args = parts[1:]

        if action == "search":
            item = args[0]

        elif action == "clear":
            clear_screen()


if __name__ == "__main__":
    try:
        wfm_cli()
    except KeyboardInterrupt:
        pass
