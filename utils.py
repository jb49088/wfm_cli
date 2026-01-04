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
                "quantity": listing.get("quantity", 1),
                "rank": listing.get("rank"),
                "visible": listing.get("visible", False),
                "created": listing.get("createdAt", ""),
                "updated": listing.get("updatedAt", ""),
            }

    return user_listings


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
        if listing.endswith(" Set"):
            set_base = get_base_name(listing)
            for item in all_items:
                item_name = item["i18n"]["en"]["name"]
                item_base = get_base_name(item_name)
                if set_base == item_base and item_name != listing:
                    expanded_listings.append(item_name)
        else:
            expanded_listings.append(listing)

    return expanded_listings
