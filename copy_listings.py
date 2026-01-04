import pyperclip

from utils import (
    build_id_to_name_mapping,
    expand_item_sets,
    extract_user_listings,
    get_all_items,
)


def convert_listings_to_links(listings):
    """Sort and format item names with surrounding brackets."""
    links = ["[" + listing + "]" for listing in listings]

    return sorted(links)


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


def copy_listings():
    """Main entry point."""
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    user_listings = extract_user_listings("bhwsg", id_to_name)
    expanded_listings = expand_item_sets(user_listings, all_items)
    links = convert_listings_to_links(expanded_listings)
    link_chunks = chunk_links(links)
    copy_to_clipboard(link_chunks)


if __name__ == "__main__":
    copy_listings()
