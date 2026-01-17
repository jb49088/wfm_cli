from typing import Any

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
    "visibility",
    "updated",
]

ARROW_MAPPING = {"desc": "↓", "asc": "↑"}


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def build_authenticated_headers(cookies: dict[str, str]) -> dict[str, str]:
    """Build authenticated headers with cookies."""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://warframe.market/",
        "language": "en",
        "platform": "pc",
        "crossplay": "true",
        "Origin": "https://warframe.market",
        "Cookie": f"JWT={cookies['jwt']}; cf_clearance={cookies['cf']}",
    }

    headers.update(BROWSER_HEADERS)

    return headers


def extract_user_listings(
    user: str, id_to_name: dict[str, str], headers
) -> list[dict[str, Any]]:
    """Extract and process listings for a specific user."""
    r = requests.get(
        url=f"https://api.warframe.market/v2/orders/user/{user.lower()}",
        headers=headers,
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
                    "visible": listing.get("visible", False),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return user_listings


def filter_listings(
    listings: list[dict[str, Any]], rank: int | None, status: str
) -> list[dict[str, Any]]:
    if rank is not None:
        listings = [listing for listing in listings if listing.get("rank") == rank]
    if status != "all":
        listings = [listing for listing in listings if listing.get("status") == status]

    return listings


def sort_listings(
    listings: list[dict[str, Any]],
    sort_by: str,
    order: str | None,
    default_orders: dict[str, str],
) -> tuple[list[dict[str, Any]], str]:
    if order is None:
        order = default_orders[sort_by]

    is_desc = order == "desc"

    sorted_listings = sorted(
        listings, key=lambda listing: listing["updated"], reverse=True
    )

    def get_sort_key(listing):
        if listing[sort_by] is None:
            return float("-inf") if is_desc else float("inf")

        if sort_by == "visibility":
            return "visible" if listing["visible"] else "hidden"

        return listing[sort_by]

    sorted_listings = sorted(
        sorted_listings,
        key=get_sort_key,
        reverse=is_desc,
    )

    return (sorted_listings, order)


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
