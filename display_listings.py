import pyperclip
import requests


def build_id_to_name_mapping() -> dict[str, str]:
    """Build id to name mapping dictionary."""
    r = requests.get("https://api.warframe.market/v2/items")
    r.raise_for_status()

    id_to_name = {}

    id_to_name = {item["id"]: item["i18n"]["en"]["name"] for item in r.json()["data"]}

    return id_to_name


def gather_user_listings(user: str) -> list[str]:
    """Gather listings for a specific user."""
    r = requests.get(f"https://api.warframe.market/v2/orders/user/{user.lower()}")
    r.raise_for_status()

    listings = [item["itemId"] for item in r.json()["data"]]

    return listings


def convert_ids_to_item_names(
    id_to_name: dict[str, str],
    listings: list[str],
) -> list[str]:
    """Convert listing IDs to in-game item names, alphabetically sorted."""
    items = [id_to_name[listing] for listing in listings]

    return sorted(items)


def format_items(items: list[str]) -> list[str]:
    """Format items with surrounding brackets."""
    formatted_items = ["[" + listing + "]" for listing in items]

    return formatted_items


def chunk_items(formatted_items: list[str]) -> list[str]:
    """Break item list into 300 character chunks."""
    chunks = []
    current_chunk = []
    current_length = 0

    for item in formatted_items:
        item_length = len(item) + 1  # +1 for the space

        if current_length + item_length > 300:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(item)
        current_length += item_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def copy_items(chunks: list[str]) -> None:
    """Copy items to clipboard."""
    for i, chunk in enumerate(chunks, 1):
        pyperclip.copy(chunk)
        if i < len(chunks):
            input(
                f"Chunk {i}/{len(chunks)} copied ({len(chunk)} chars). Press Enter for next chunk..."
            )
        else:
            print(f"Chunk {i}/{len(chunks)} copied ({len(chunk)} chars).")


def main() -> None:
    """Main entry point."""
    id_to_name = build_id_to_name_mapping()
    listings = gather_user_listings("bhwsg")
    items = convert_ids_to_item_names(id_to_name, listings)
    formatted_items = format_items(items)
    chunks = chunk_items(formatted_items)
    copy_items(chunks)


if __name__ == "__main__":
    main()
