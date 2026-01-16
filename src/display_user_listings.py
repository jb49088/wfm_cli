from typing import Any

import pyperclip

from utils import (
    determine_widths,
    display_listings,
    extract_user_listings,
    filter_listings,
    sort_listings,
)

DEFAULT_ORDERS = {
    "item": "asc",
    "price": "desc",
    "rank": "desc",
    "quantity": "desc",
    "created": "desc",
    "visibility": "desc",
    "updated": "desc",
}

RIGHT_ALLIGNED_COLUMNS = ("price", "rank", "quantity")


def build_rows(
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


def copy_listing(user: str, data_rows: list[dict[str, str]]) -> None:
    """Prompt for and copy a listing."""
    listing = input("Listing to copy: ").strip()

    for row in data_rows:
        if row["#"] == listing:
            segments = [
                "WTB",
                f"{row['item']}",
                f"Rank: {row['rank']}" if row.get("rank") else "",
                f"Price: {row['price']}",
            ]
            segments = [s for s in segments if s]
            message = f"/w {user} {' | '.join(segments)}"
            pyperclip.copy(message)
            print(f"Copied to clipboard: {message}")
            return

    print(f"Listing {listing} not found")


def display_user_listings(
    id_to_name: dict[str, str],
    max_ranks: dict[str, int | None],
    user: str,
    rank: int | None = None,
    sort: str = "updated",
    order: str | None = None,
) -> None:
    """Main entry point."""
    user_listings = extract_user_listings(user, id_to_name)
    filtered_item_listings = filter_listings(user_listings, rank, status="all")
    sorted_user_listings, sort_order = sort_listings(
        filtered_item_listings, sort, order, DEFAULT_ORDERS
    )
    data_rows = build_rows(sorted_user_listings, max_ranks)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, sort_order)
