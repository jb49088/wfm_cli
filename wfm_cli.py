# ================================================================================
# =                                   WFM_CLI                                    =
# ================================================================================

from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings
from menu import menu


def wfm_cli():
    menu()
    option = input("Option > ")
    if option == "1":
        item = input("Item > ")
        display_item_listings(item)
    elif option == "2":
        pass


if __name__ == "__main__":
    wfm_cli()
