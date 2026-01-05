import requests


def get_all_items():
    """Extract all raw item data."""
    r = requests.get("https://api.warframe.market/v2/items")
    r.raise_for_status()

    return r.json()["data"]


def build_id_to_name_mapping(all_items):
    """Build id to name mapping dictionary."""
    return {item["id"]: item["i18n"]["en"]["name"] for item in all_items}


def extract_user_listings(user, id_to_name):
    """Extract and process listings for a specific user."""
    r = requests.get(f"https://api.warframe.market/v2/orders/user/{user.lower()}")
    r.raise_for_status()

    user_listings = {}

    for listing in r.json()["data"]:
        if listing["type"] == "sell":
            user_listings[id_to_name[listing["itemId"]]] = {
                "price": listing.get("platinum", 0),
                "rank": listing.get("rank"),
                "quantity": listing.get("quantity", 1),
                "visible": listing.get("visible", False),
                "created": listing.get("createdAt", ""),
                "updated": listing.get("updatedAt", ""),
            }

    return user_listings
