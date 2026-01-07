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

    user_listings = []

    for listing in r.json()["data"]:
        if listing["type"] == "sell":
            user_listings.append(
                {
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "price": listing.get("platinum", 0),
                    "rank": listing.get("rank"),
                    "quantity": listing.get("quantity", 1),
                    "created": listing.get("createdAt", ""),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return user_listings


def sort_user_listings(listings, sort_by="updated", order=None):
    """Sort listings with sane defaults."""
    default_orders = {
        "item": "asc",
        "price": "desc",
        "rank": "desc",
        "quantity": "desc",
        "created": "desc",
        "updated": "desc",
    }

    is_desc = (default_orders[sort_by] == "desc") if not order else (order == "desc")

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

    return (sorted_listings, sort_by, default_orders[sort_by] if not order else order)
