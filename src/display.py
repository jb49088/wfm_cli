from typing import Any

COLUMNS = [
    "#",
    "seller",
    "reputation",
    "status",
    "item",
    "price",
    "rank",
    "quantity",
    "visibility",
    "updated",
]
ARROW_MAPPING = {"desc": "↓", "asc": "↑"}

DEFAULT_ORDERS = {
    "seller": "asc",
    "reputation": "desc",
    "status": "asc",
    "item": "asc",
    "price": "asc",
    "rank": "desc",
    "quantity": "desc",
    "visibility": "desc",
    "created": "desc",
    "updated": "desc",
}

RIGHT_ALLIGNED_COLUMNS = ("price", "quantity", "reputation")

STATUS_MAPPING = {"offline": "Offline", "online": "Online", "ingame": "In Game"}


# ================================= ROW BUILDERS =================================


def build_seller_rows(
    listings: list[dict[str, Any]], max_ranks: dict[str, int | None]
) -> list[dict[str, str]]:
    """Build rows for table rendering."""
    show_rank = any(listing.get("rank") is not None for listing in listings)
    data_rows = []
    for i, listing in enumerate(listings, start=1):
        row = {
            "#": str(i),
            "item": listing["item"],
            "price": f"{listing['price']}p",
            "quantity": str(listing["quantity"]),
            "updated": str(listing["updated"]),
        }

        if show_rank and listing.get("rank") is not None:
            row["rank"] = f"{listing['rank']}/{max_ranks[listing['item']]}"

        data_rows.append(row)

    return data_rows


def build_listings_rows(
    listings: list[dict[str, Any]], max_ranks: dict[str, int | None]
) -> list[dict[str, str]]:
    """Build rows for table rendering."""
    show_rank = any(listing.get("rank") is not None for listing in listings)
    data_rows = []
    for i, listing in enumerate(listings, start=1):
        row = {
            "#": str(i),
            "item": listing["item"],
            "price": f"{listing['price']}p",
            "quantity": str(listing["quantity"]),
            "visibility": "Visible" if listing["visible"] else "Hidden",
            "updated": str(listing["updated"]),
        }

        if show_rank and listing.get("rank") is not None:
            row["rank"] = f"{listing['rank']}/{max_ranks[listing['item']]}"

        data_rows.append(row)

    return data_rows


def build_search_rows(
    listings: list[dict[str, Any]], max_ranks: dict[str, int | None]
) -> list[dict[str, str]]:
    """Build rows for table rendering."""
    data_rows = []
    for i, listing in enumerate(listings, start=1):
        row = {
            "#": str(i),
            "seller": listing["seller"],
            "reputation": str(listing["reputation"]),
            "status": STATUS_MAPPING[listing["status"]],
            "item": listing["item"],
            "price": f"{listing['price']}p",
            "quantity": str(listing["quantity"]),
            "updated": str(listing["updated"]),
        }

        if listing.get("rank") is not None:
            row["rank"] = f"{listing['rank']}/{max_ranks[listing['item']]}"

        data_rows.append(row)

    return data_rows


# =============================== TABLE RENDERING ================================


def determine_widths(data_rows: list[dict[str, Any]], sort_by: str) -> dict[str, int]:
    """Determine maximum width for each colunm."""
    active_columns = [col for col in COLUMNS if any(col in row for row in data_rows)]

    column_widths = {col: 0 for col in active_columns}

    for row in data_rows:
        for col in active_columns:
            column_widths[col] = max(
                column_widths[col],
                len(str(row.get(col, ""))),
                len(col) + 2 if col == sort_by else len(col),  # +2 for arrow
            )

    # Account for spacing
    column_widths = {key: width + 2 for key, width in column_widths.items()}

    return column_widths


def display_listings(
    data_rows: list[dict[str, Any]],
    column_widths: dict[str, int],
    right_alligned_columns: tuple[str, ...],
    sort_by: str,
    sort_order: str,
) -> None:
    """Display listings in a sql-like table."""
    separator_row = ["-" * width for width in column_widths.values()]

    header_row = [
        f"{key} {ARROW_MAPPING[sort_order]}".title().center(width)
        if key == sort_by
        else key.title().center(width)
        for key, width in column_widths.items()
    ]

    print()
    print(f"+{'+'.join(separator_row)}+")
    print(f"|{'|'.join(header_row)}|")
    print(f"+{'+'.join(separator_row)}+")

    for row in data_rows:
        data_row = []
        for key in column_widths:
            value = row.get(key, "")

            if key in right_alligned_columns:
                formatted = f"{value} ".rjust(column_widths[key])
            else:
                formatted = f" {value}".ljust(column_widths[key])

            data_row.append(formatted)

        print(f"|{'|'.join(data_row)}|")

    print(f"+{'+'.join(separator_row)}+")
    print()


# =============================== SIMPLE DISPLAYS ================================


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


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
        "  search <item|number> [sort <field>] [order <asc|desc>] [rank <number>] [status <all|ingame|online|offline>]"
    )
    print("      Search for item listings (all filters optional)")
    print('      Example: search "ammo drum"')
    print('      Example: search "ammo drum" rank 5 sort reputation')
    print("      Example: search serration rank 0 status ingame")
    print("      Example: search 3  (searches item at position 3 from current results)")
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
    print("  links")
    print("      Generate formatted item links from your listings for in-game chat")
    print("      Expands sets into individual parts and chunks into 300-char messages")
    print("      Example: links")
    print()
    print("  sync")
    print("      Update your listings based on completed trades from game log")
    print("      Example: sync")
    print()
    print("  status <ingame|online|invisible>")
    print("      Change your online status on Warframe Market")
    print("      Example: status ingame")
    print("      Example: status invisible")
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
