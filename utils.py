import requests

ARROW_MAPPING = {"desc": "↓", "asc": "↑"}


def get_all_items():
    """Extract all raw item data."""
    r = requests.get("https://api.warframe.market/v2/items")
    r.raise_for_status()

    return r.json()["data"]


def build_id_to_name_mapping(all_items):
    """Build a mapping from item ID to in game name."""
    return {item["id"]: item["i18n"]["en"]["name"] for item in all_items}


def build_name_to_max_rank_mapping(all_items, id_to_name):
    """Build a mapping from item name to max rank."""
    return {id_to_name[item["id"]]: item.get("maxRank") for item in all_items}


def extract_user_listings(user, id_to_name):
    """Extract and process listings for a specific user."""
    r = requests.get(f"https://api.warframe.market/v2/orders/user/{user.lower()}")
    r.raise_for_status()

    user_listings = []

    for listing in r.json()["data"]:
        if listing["type"] == "sell":
            user_listings.append(
                {
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "price": listing.get("platinum", 0),
                    "rank": listing.get("rank"),
                    "quantity": listing.get("quantity", 1),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return user_listings


def sort_user_listings(listings, sort_by="updated", order=None):
    """Sort listings with sane defaults."""
    default_orders = {
        "item": "asc",
        "price": "desc",
        "rank": "desc",
        "quantity": "desc",
        "created": "desc",
        "updated": "desc",
    }

    is_desc = (default_orders[sort_by] == "desc") if not order else (order == "desc")

    sorted_listings = list(
        sorted(
            listings,
            key=lambda listing: listing[sort_by]
            if listing[sort_by] is not None
            else float("-inf")
            if is_desc
            else float("inf"),
            reverse=is_desc,
        )
    )

    return (sorted_listings, sort_by, default_orders[sort_by] if not order else order)


def determine_widths(data_rows, sort_by):
    """Determine maximum width for each colunm."""
    column_widths = {key: 0 for key in data_rows[0]}

    for row in data_rows:
        for key in row:
            column_widths[key] = max(
                column_widths[key],
                len(row[key]),
                len(key) + 2 if key == sort_by else len(key),  # +2 for arrow
            )

    # Account for spacing
    column_widths = {key: width + 2 for key, width in column_widths.items()}

    return column_widths


def display_listings(data_rows, column_widths, right_alligned_columns, sort_by, order):
    """Display listings in a sql-like table."""
    separator_row = ["-" * width for width in column_widths.values()]

    header_row = [
        f"{key} {ARROW_MAPPING[order]}".title().center(width)
        if key == sort_by
        else key.title().center(width)
        for key, width in column_widths.items()
    ]

    print(f"+{'+'.join(separator_row)}+")
    print(f"|{'|'.join(header_row)}|")
    print(f"+{'+'.join(separator_row)}+")

    for row in data_rows:
        data_row = []
        for key, value in row.items():
            if key in right_alligned_columns:
                formatted = f"{value} ".rjust(column_widths[key])
            else:
                formatted = f" {value}".ljust(column_widths[key])
            data_row.append(formatted)

        print(f"|{'|'.join(data_row)}|")

    print(f"+{'+'.join(separator_row)}+")
