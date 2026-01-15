import requests

from config import BROWSER_HEADERS

COLUMNS = [
    "#",
    "seller",
    "reputation",
    "status",
    "item",
    "price",
    "rank",
    "quantity",
    "updated",
]

ARROW_MAPPING = {"desc": "↓", "asc": "↑"}


def clear_screen():
    print("\033[2J\033[H", end="")


def extract_user_listings(user, id_to_name):
    """Extract and process listings for a specific user."""
    r = requests.get(
        url=f"https://api.warframe.market/v2/orders/user/{user.lower()}",
        headers=BROWSER_HEADERS,
    )
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


def filter_listings(item_listings, rank, status):
    """Filter listings."""
    if rank is not None:
        item_listings = [
            listing for listing in item_listings if listing.get("rank") == rank
        ]
    if status != "all":
        item_listings = [
            listing for listing in item_listings if listing.get("status") == status
        ]

    return item_listings


def sort_listings(listings, sort_by, order, default_orders):
    """Sort listings."""
    if order is None:
        order = default_orders[sort_by]

    is_desc = order == "desc"

    sorted_listings = sorted(
        listings, key=lambda listing: listing["updated"], reverse=True
    )

    sorted_listings = sorted(
        sorted_listings,
        key=lambda listing: listing[sort_by]
        if listing[sort_by] is not None
        else float("-inf")
        if is_desc
        else float("inf"),
        reverse=is_desc,
    )

    return (sorted_listings, sort_by, order)


def determine_widths(data_rows, sort_by):
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
        for key in column_widths:
            value = row.get(key, "")

            if key in right_alligned_columns:
                formatted = f"{value} ".rjust(column_widths[key])
            else:
                formatted = f" {value}".ljust(column_widths[key])

            data_row.append(formatted)

        print(f"|{'|'.join(data_row)}|")

    print(f"+{'+'.join(separator_row)}+")
