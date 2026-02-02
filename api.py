from typing import Any

import aiohttp

from config import USER_AGENT

# =================================== METADATA ===================================


async def get_user_info(
    session: aiohttp.ClientSession, headers: dict[str, str]
) -> dict[str, Any]:
    """Get the authenticated users profile info."""
    async with session.get(
        url="https://api.warframe.market/v2/me", headers=headers
    ) as r:
        r.raise_for_status()
        data = (await r.json())["data"]

        return {
            "ingameName": data.get("ingameName", "Unknown"),
            "slug": data["slug"],
            "reputation": data.get("reputation", 0),
            "platform": data["platform"],
            "crossplay": data.get("crossplay", False),
        }


async def get_all_items(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    """Extract all raw item data."""
    async with session.get(
        url="https://api.warframe.market/v2/items", headers=USER_AGENT
    ) as r:
        r.raise_for_status()

        return (await r.json())["data"]


# =============================== DATA EXTRACTION ================================


async def extract_user_listings(
    session: aiohttp.ClientSession, user: str, id_to_name: dict[str, str], headers
) -> list[dict[str, Any]]:
    """Extract and process listings for a specific user."""
    async with session.get(
        url=f"https://api.warframe.market/v2/orders/user/{user}",
        headers=headers,
    ) as r:
        r.raise_for_status()
        response_data = await r.json()

    user_listings = []
    for listing in response_data["data"]:
        if listing["type"] == "sell":
            user_listings.append(
                {
                    "id": listing.get("id", ""),
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "price": listing.get("platinum", 0),
                    "rank": listing.get("rank"),
                    "quantity": listing.get("quantity", 1),
                    "visible": listing.get("visible", False),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return user_listings


async def extract_item_listings(
    session: aiohttp.ClientSession, item: str, id_to_name: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract and process listings for a specific item."""
    async with session.get(
        url=f"https://api.warframe.market/v2/orders/item/{item}",
        headers=USER_AGENT,
    ) as r:
        r.raise_for_status()
        response_data = await r.json()

    item_listings = []
    for listing in response_data["data"]:
        if listing["type"] == "sell":
            item_listings.append(
                {
                    "seller": listing.get("user", {}).get("ingameName", "Unknown"),
                    "slug": listing.get("user", {}).get("slug", "Unknown"),
                    "reputation": listing.get("user", {}).get("reputation", 0),
                    "status": listing.get("user", {}).get("status", "offline"),
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "rank": listing.get("rank"),
                    "price": listing.get("platinum", 0),
                    "quantity": listing.get("quantity", 1),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return item_listings


async def extract_seller_listings(
    session: aiohttp.ClientSession, slug: str, seller: str, id_to_name: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract and process listings for a specific user."""
    async with session.get(
        url=f"https://api.warframe.market/v2/orders/user/{slug}",
        headers=USER_AGENT,
    ) as r:
        r.raise_for_status()
        response_data = await r.json()

    user_listings = []
    for listing in response_data["data"]:
        if listing["type"] == "sell":
            user_listings.append(
                {
                    "seller": seller,
                    "item": id_to_name[listing.get("itemId", "")],
                    "itemId": listing.get("itemId", ""),
                    "price": listing.get("platinum", 0),
                    "rank": listing.get("rank"),
                    "quantity": listing.get("quantity", 1),
                    "updated": listing.get("updatedAt", ""),
                }
            )

    return user_listings


# ============================== LISTING MANAGEMENT ==============================


async def add_listing(
    session: aiohttp.ClientSession,
    headers: dict[str, str],
    item_id: str,
    price: int,
    quantity: int,
    rank: int | None = None,
    per_trade: int | None = None,
) -> None:
    payload = {
        "itemId": item_id,
        "platinum": price,
        "quantity": quantity,
        "type": "sell",
        "visible": True,
    }

    if rank is not None:
        payload["rank"] = rank

    if per_trade is not None:
        payload["perTrade"] = per_trade

    async with session.post(
        "https://api.warframe.market/v2/order", json=payload, headers=headers
    ) as r:
        r.raise_for_status()


async def change_visibility(
    session: aiohttp.ClientSession,
    listing_id: str,
    visibility: bool,
    headers: dict[str, str],
) -> None:
    async with session.patch(
        url=f"https://api.warframe.market/v2/order/{listing_id}",
        json={"visible": visibility},
        headers=headers,
    ) as r:
        r.raise_for_status()


async def change_all_visibility(
    session: aiohttp.ClientSession, visibility: bool, headers: dict[str, str]
) -> None:
    async with session.patch(
        url="https://api.warframe.market/v2/orders/group/all",
        json={"type": "sell", "visible": visibility},
        headers=headers,
    ) as r:
        r.raise_for_status()


async def delete_listing(
    session: aiohttp.ClientSession, listing_id: str, headers: dict[str, str]
) -> None:
    async with session.delete(
        url=f"https://api.warframe.market/v2/order/{listing_id}",
        headers=headers,
    ) as r:
        r.raise_for_status()


async def edit_listing(
    session: aiohttp.ClientSession,
    headers: dict[str, str],
    listing_id: str,
    price: int,
    quantity: int,
    rank: int,
    visible: bool,
) -> None:
    payload = {
        "platinum": price,
        "quantity": quantity,
        "rank": rank,
        "visible": visible,
    }

    async with session.patch(
        url=f"https://api.warframe.market/v2/order/{listing_id}",
        headers=headers,
        json=payload,
    ) as r:
        r.raise_for_status()
