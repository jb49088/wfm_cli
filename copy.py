import pyperclip

from utils import (
    build_id_to_name_mapping,
    extract_user_listings,
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


def get_base_name(item_name):
    """Extract base name without part suffixes."""
    part_words = [
        "Set",
        "Blueprint",
        "Barrel",
        "Receiver",
        "Stock",
        "Neuroptics",
        "Chassis",
        "Systems",
        "Link",
        "Wings",
        "Harness",
        "Grip",
        "Blade",
        "Lower Limb",
        "Handle",
        "Upper Limb",
        "String",
    ]
    words = item_name.split()
    # Remove known part words from the end
    while words and words[-1] in part_words:
        words.pop()

    return " ".join(words)


def expand_item_sets(user_listings, all_items):
    """Expand set items into individual parts for the set."""
    expanded_listings = []

    for listing in user_listings:
        if listing["item"].endswith(" Set"):
            set_base = get_base_name(listing["item"])
            for item in all_items:
                item_name = item["i18n"]["en"]["name"]
                item_base = get_base_name(item_name)
                if set_base == item_base and item_name != listing["item"]:
                    expanded_listings.append(item_name)
        else:
            expanded_listings.append(listing["item"])

    return expanded_listings


def convert_listings_to_links(listings):
    """Process and format item names for ingame pasting."""
    return [
        f"[{listing.replace(' Blueprint', '')}]"
        if "Blueprint" in listing
        else f"[{listing}]"
        for listing in listings
    ]


def chunk_links(links):
    """Break item list into 300 character chunks."""
    chunks = []
    current_chunk = []
    current_length = 0

    for link in links:
        link_length = len(link) + 1  # +1 for the space
        if current_length + link_length > 300:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(link)
        current_length += link_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def copy_to_clipboard(chunks):
    """Copy items to clipboard."""
    for i, chunk in enumerate(chunks, 1):
        pyperclip.copy(chunk)
        if i < len(chunks):
            input(
                f"Chunk {i}/{len(chunks)} copied ({len(chunk)} chars). Press Enter for next chunk..."
            )
        else:
            print(f"Chunk {i}/{len(chunks)} copied ({len(chunk)} chars).")


def copy_user_listings(args):
    """Main entry point."""
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    user_listings = extract_user_listings(args.user, id_to_name)
    sorted_user_listings = sort_listings(
        user_listings, args.sort, args.order, DEFAULT_ORDERS
    )
    expanded_listings = expand_item_sets(sorted_user_listings, all_items)
    links = convert_listings_to_links(expanded_listings)
    link_chunks = chunk_links(links)
    copy_to_clipboard(link_chunks)
