from typing import Any

import requests

from config import BROWSER_HEADERS
from utils import (
    determine_widths,
    display_listings,
    filter_listings,
    sort_listings,
)

DEFAULT_ORDERS = {
    "item": "asc",
    "price": "desc",
    "rank": "desc",
    "quantity": "desc",
    "created": "desc",
    "updated": "desc",
}

RIGHT_ALLIGNED_COLUMNS = ("price", "quantity")


def extract_seller_listings(
    slug: str, seller: str, id_to_name: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract and process listings for a specific user."""
    r = requests.get(
        url=f"https://api.warframe.market/v2/orders/user/{slug}",
        headers=BROWSER_HEADERS,
    )
    r.raise_for_status()

    user_listings = []

    for listing in r.json()["data"]:
        if listing["type"] == "sell":
            user_listings.append(
                {
                    "seller": seller,
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "price": listing.get("platinum", 0),
                    "rank": listing.get("rank"),
                    "quantity": listing.get("quantity", 1),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return user_listings


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
            "updated": str(listing["updated"]),
        }

        if show_rank and listing.get("rank") is not None:
            row["rank"] = f"{listing['rank']}/{max_ranks[listing['item']]}"

        data_rows.append(row)

    return data_rows


def seller(
    id_to_name: dict[str, str],
    max_ranks: dict[str, int | None],
    slug: str,
    seller: str,
    rank: int | None = None,
    sort: str = "updated",
    order: str | None = None,
) -> list[dict[str, Any]]:
    """Main entry point."""
    seller_listings = extract_seller_listings(slug, seller, id_to_name)
    filtered_seller_listings = filter_listings(seller_listings, rank, status="all")
    sorted_seller_listings, sort_order = sort_listings(
        filtered_seller_listings, sort, order, DEFAULT_ORDERS
    )
    data_rows = build_rows(sorted_seller_listings, max_ranks)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, sort_order)

    return sorted_seller_listings
