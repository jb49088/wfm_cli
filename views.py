from utils import clear_screen

MENU_OPTIONS = [
    "Search for item",
    "Show my listings",
    "Sync my listings",
    "Change my status",
    "Authenticate",
    "Profile",
    "Log out",
    "Quit",
]


def menu():
    clear_screen()
    print("wfm_cli")
    print()
    for i, option in enumerate(MENU_OPTIONS, 1):
        print(f"{i}. {option}")
    print()
