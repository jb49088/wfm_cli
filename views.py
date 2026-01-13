from utils import clear_screen

MENU_OPTIONS = [
    "Search",
    "Listings",
    "Sync listings",
    "Change status",
    "Profile",
    "Quit",
]


def menu():
    clear_screen()

    left = "wfm_cli"
    right = "In-Game"

    # Determine menu width
    menu_width = max(len(option) for option in MENU_OPTIONS + [left, right]) + 3

    # Align header
    spacing = menu_width - len(left) - len(right)
    print(f"{left}{' ' * spacing}{right}")
    print()

    # Menu options
    for i, option in enumerate(MENU_OPTIONS, 1):
        print(f"{i}. {option}")
    print()


def profile():
    clear_screen()
    print("Profile")
    print()
    print("Name: Username123")
    print("Reputation: 1337")
    print("Platform: PC")
    print("Crossplay: On")
    print()
