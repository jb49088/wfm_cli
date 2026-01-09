import pyperclip
import requests

from utils import (
    build_id_to_name_mapping,
    build_name_to_max_rank_mapping,
    determine_widths,
    display_listings,
    get_all_items,
)

STATUS_MAPPING = {"offline": "Offline", "online": "Online", "ingame": "In Game"}
RIGHT_ALLIGNED_COLUMNS = ("price", "rank", "quantity", "reputation")


def extract_item_listings(item, id_to_name):
    """Extract and process listings for a specific item."""
    r = requests.get(f"https://api.warframe.market/v2/orders/item/{item.lower()}")
    r.raise_for_status()

    item_listings = []

    for listing in r.json()["data"]:
        if listing["type"] == "sell":
            item_listings.append(
                {
                    "seller": listing.get("user", {}).get("ingameName", "Unknown"),
                    "reputation": listing.get("user", {}).get("reputation", 0),
                    "status": listing.get("user", {}).get("status", "offline"),
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "price": listing.get("platinum", 0),
                    "rank": listing.get("rank"),
                    "quantity": listing.get("quantity", 1),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return item_listings


def filter_item_listings(item_listings, ingame_only):
    """Filter out listings for sellers that are not in game."""
    if ingame_only:
        item_listings = [
            listing for listing in item_listings if listing["status"] == "ingame"
        ]
    return item_listings


def sort_item_listings(listings, sort_by, order):
    """Sort listings with sane defaults."""
    default_orders = {
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

    # Use default order if none provided
    if order is None:
        order = default_orders[sort_by]

    is_desc = order == "desc"

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

    return (sorted_listings, sort_by, order)


def build_rows(listings, max_ranks, copy):
    """Build rows for table rendering."""
    data_rows = []
    for i, listing in enumerate(listings, start=1):
        row = {
            "#": str(i),
            "seller": listing["seller"],
            "status": STATUS_MAPPING[listing["status"]],
            "item": listing["item"],
            "price": f"{listing['price']}p",
            "rank": f"{listing['rank']}/{max_ranks[listing['item']]}"
            if listing["rank"] is not None
            else "",
            "quantity": str(listing["quantity"]),
            "reputation": str(listing["reputation"]),
            "updated": str(listing["updated"]),
        }
        if not copy:
            del row["#"]
        data_rows.append(row)

    return data_rows


def copy_listing(data_rows):
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
            message = f"/w {row['seller']} {' | '.join(segments)}"
            pyperclip.copy(message)
            print(f"Copied to clipboard: {message}")
            return

    print(f"Listing {listing} not found")


def display_item_listings(
    item="Lohk", sort_by="price", order=None, ingame_only=True, copy=True
):
    """Main entry point."""
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    max_ranks = build_name_to_max_rank_mapping(all_items, id_to_name)
    item_listings = extract_item_listings(item, id_to_name)
    filtered_item_listings = filter_item_listings(item_listings, ingame_only)
    sorted_item_listings, sort_by, order = sort_item_listings(
        filtered_item_listings, sort_by, order
    )
    data_rows = build_rows(sorted_item_listings, max_ranks, copy)
    column_widths = determine_widths(data_rows, sort_by)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort_by, order)
    if copy:
        copy_listing(data_rows)


if __name__ == "__main__":
    display_item_listings()
