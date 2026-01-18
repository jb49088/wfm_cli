from typing import Any

import pyperclip
import requests

from config import BROWSER_HEADERS
from utils import (
    determine_widths,
    display_listings,
    filter_listings,
    sort_listings,
)

DEFAULT_ORDERS = {
    "seller": "asc",
    "reputation": "desc",
    "status": "asc",
    "item": "asc",
    "price": "asc",
    "rank": "desc",
    "quantity": "desc",
    "created": "desc",
    "updated": "desc",
}
STATUS_MAPPING = {"offline": "Offline", "online": "Online", "ingame": "In Game"}
RIGHT_ALLIGNED_COLUMNS = ("price", "quantity", "reputation")


def slugify_item_name(item: str) -> str:
    """Convert item name to URL-safe slug."""
    return item.lower().replace(" ", "_")


def extract_item_listings(
    item: str, id_to_name: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract and process listings for a specific item."""
    r = requests.get(
        url=f"https://api.warframe.market/v2/orders/item/{item}",
        headers=BROWSER_HEADERS,
    )
    r.raise_for_status()

    item_listings = []

    for listing in r.json()["data"]:
        if listing["type"] == "sell":
            item_listings.append(
                {
                    "seller": listing.get("user", {}).get("ingameName", "Unknown"),
                    "slug": listing.get("user", {}).get("slug", "Unknown"),
                    "reputation": listing.get("user", {}).get("reputation", 0),
                    "status": listing.get("user", {}).get("status", "offline"),
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "rank": listing.get("rank"),
                    "price": listing.get("platinum", 0),
                    "quantity": listing.get("quantity", 1),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return item_listings


def build_rows(
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


def copy(
    listing: str, listings: list[dict[str, Any]], max_ranks: dict[str, int | None]
) -> None:
    """Copy a listing for in-game whispering."""
    listing_to_copy = listings[int(listing) - 1]

    item_name = listing_to_copy["item"]

    if listing_to_copy.get("rank") is not None:
        item_name = (
            f"{item_name} (rank {listing_to_copy['rank']}/{max_ranks[item_name]})"
        )

    segments = [
        "WTB",
        item_name,
        f"{listing_to_copy['price']}p",
    ]
    message = f"/w {listing_to_copy['seller']} {' | '.join(segments)}"

    pyperclip.copy(message)

    print(f"\nCopied to clipboard: {message}\n")


def search(
    id_to_name: dict[str, str],
    max_ranks: dict[str, int | None],
    item: str,
    rank: int | None = None,
    sort: str = "price",
    order: str | None = None,
    status: str = "ingame",
) -> list[dict[str, Any]]:
    """Main entry point."""
    item_slug = slugify_item_name(item)
    item_listings = extract_item_listings(item_slug, id_to_name)
    filtered_item_listings = filter_listings(item_listings, rank, status)
    sorted_item_listings, sort_order = sort_listings(
        filtered_item_listings, sort, order, DEFAULT_ORDERS
    )
    data_rows = build_rows(sorted_item_listings, max_ranks)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, sort_order)

    return sorted_item_listings
