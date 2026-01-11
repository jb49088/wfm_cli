import pyperclip

from utils import (
    build_id_to_name_mapping,
    build_name_to_max_rank_mapping,
    determine_widths,
    display_listings,
    extract_user_listings,
    filter_listings,
    get_all_items,
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
RIGHT_ALLIGNED_COLUMNS = ("price", "rank", "quantity")


def build_rows(listings, max_ranks, copy):
    """Build rows for table rendering."""
    show_rank = any(listing.get("rank") is not None for listing in listings)
    data_rows = []
    for i, listing in enumerate(listings, start=1):
        row = {}

        if copy:
            row["#"] = str(i)

        row["item"] = listing["item"]
        row["price"] = f"{listing['price']}p"

        if show_rank and listing.get("rank") is not None:
            row["rank"] = f"{listing['rank']}/{max_ranks[listing['item']]}"

        row["quantity"] = str(listing["quantity"])
        row["updated"] = str(listing["updated"])

        data_rows.append(row)

    return data_rows


def copy_listing(user, data_rows):
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


def display_user_listings(args):
    """Main entry point."""
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    max_ranks = build_name_to_max_rank_mapping(all_items, id_to_name)
    user_listings = extract_user_listings(args.user, id_to_name)
    filtered_item_listings = filter_listings(user_listings, args.rank, in_game=False)
    sorted_user_listings, sort, order = sort_listings(
        filtered_item_listings, args.sort, args.order, DEFAULT_ORDERS
    )
    data_rows = build_rows(sorted_user_listings, max_ranks, args.copy)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, order)
    if args.copy:
        copy_listing(args.user, data_rows)
