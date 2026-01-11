import pyperclip
import requests

from utils import (
    build_id_to_name_mapping,
    build_name_to_max_rank_mapping,
    determine_widths,
    display_listings,
    filter_listings,
    get_all_items,
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
RIGHT_ALLIGNED_COLUMNS = ("price", "rank", "quantity", "reputation")


def slugify_item_name(item):
    """Convert item name to URL-safe slug."""
    return item.lower().replace(" ", "_")


def extract_item_listings(item, id_to_name):
    """Extract and process listings for a specific item."""
    r = requests.get(f"https://api.warframe.market/v2/orders/item/{item.lower()}")
    r.raise_for_status()

    item_listings = []

    for listing in r.json()["data"]:
        if listing["type"] == "sell":
            listing_dict = {
                "seller": listing.get("user", {}).get("ingameName", "Unknown"),
                "reputation": listing.get("user", {}).get("reputation", 0),
                "status": listing.get("user", {}).get("status", "offline"),
                "item": id_to_name[listing.get("itemId", "")],
                "itemId": listing.get("itemId", ""),
                "rank": listing.get("rank"),
                "price": listing.get("platinum", 0),
                "quantity": listing.get("quantity", 1),
                "updated": listing.get("updatedAt", ""),
            }

            item_listings.append(listing_dict)

    return item_listings


def build_rows(listings, max_ranks, copy):
    """Build rows for table rendering."""
    data_rows = []
    for i, listing in enumerate(listings, start=1):
        row = {}

        if copy:
            row["#"] = str(i)

        row["seller"] = listing["seller"]
        row["reputation"] = str(listing["reputation"])
        row["status"] = STATUS_MAPPING[listing["status"]]
        row["item"] = listing["item"]

        if listing.get("rank") is not None:
            row["rank"] = f"{listing['rank']}/{max_ranks[listing['item']]}"

        row["price"] = f"{listing['price']}p"
        row["quantity"] = str(listing["quantity"])
        row["updated"] = str(listing["updated"])

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


def display_item_listings(args):
    """Main entry point."""
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    max_ranks = build_name_to_max_rank_mapping(all_items, id_to_name)
    item_slug = slugify_item_name(args.item)
    item_listings = extract_item_listings(item_slug, id_to_name)
    filtered_item_listings = filter_listings(item_listings, args.rank, args.in_game)
    sorted_item_listings, sort, order = sort_listings(
        filtered_item_listings, args.sort, args.order, DEFAULT_ORDERS
    )
    data_rows = build_rows(sorted_item_listings, max_ranks, args.copy)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, order)
    if args.copy:
        copy_listing(data_rows)
