import requests

from utils import (
    build_id_to_name_mapping,
    build_name_to_max_rank_mapping,
    get_all_items,
)


def extract_item_listings(id_to_name):
    """Extract and process listings for a specific item."""
    r = requests.get("https://api.warframe.market/v2/orders/item/lohk")
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


def display_item_listings():
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    max_ranks = build_name_to_max_rank_mapping(all_items, id_to_name)
    item_listings = extract_item_listings(id_to_name)

    print(item_listings)


if __name__ == "__main__":
    display_item_listings()
