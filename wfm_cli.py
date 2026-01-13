# ================================================================================
# =                                   WFM_CLI                                    =
# ================================================================================

import sys

from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings
from views import menu


def enter_alt_screen():
    sys.stdout.write("\033[?1049h")
    sys.stdout.flush()


def exit_alt_screen():
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()


def wfm_cli():
    menu()
    option = input("Option> ")
    if option == "1":
        item = input("Item> ")
        display_item_listings(item)
    elif option == "2":
        pass
    elif option == "7":
        exit_alt_screen()


if __name__ == "__main__":
    # enter_alt_screen()
    try:
        wfm_cli()
    except KeyboardInterrupt:
        pass
    # finally:
    #     exit_alt_screen()
