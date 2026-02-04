import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import aiohttp
import pyperclip
from prompt_toolkit import PromptSession

from api import (
    delete_listing,
    edit_listing,
    extract_item_listings,
    extract_seller_listings,
    extract_user_listings,
)
from config import SYNC_STATE_FILE
from display import (
    DEFAULT_ORDERS,
    RIGHT_ALLIGNED_COLUMNS,
    build_listings_rows,
    build_search_rows,
    build_seller_rows,
    determine_widths,
    display_listings,
)
from filters import filter_listings, sort_listings

PART_SUFFIXES = [
    "Set",
    "Blueprint",
    "Barrel",
    "Receiver",
    "Casing",
    "Pod",
    "Weapon Pod",
    "Engine",
    "Stock",
    "Neuroptics",
    "Chassis",
    "Systems",
    "Gauntlet",
    "Link",
    "Buckle",
    "Carapace",
    "Cerebrum",
    "Band",
    "Wings",
    "Pouch",
    "Stars",
    "Harness",
    "Grip",
    "Blade",
    "Lower Limb",
    "Handle",
    "Upper Limb",
    "String",
]

UNLINKABLE_ITEMS = {
    "Primed Chamber",
    "Ancient Fusion Core",
    "Legendary Fusion Core",
    "Cephalon Suda Augment Mod",
    "Steel Meridian Augment Mod",
    "The Perrin Sequence Augment Mod",
    "Arbiters of Hexis Augment Mod",
    "Red Veil Augment Mod",
    "New Loka Augment Mod",
    "Scan Aquatic Lifeforms",
    "Corpus Void Key",
    "Vay Hek Frequency Triangulator",
    "Grendel Systems Locator",
    "Grendel Chassis Locator",
    "Grendel Neuroptics Locator",
    "Companion Weapon Riven Mod (Veiled)",
    "Equilibrium (Steam Pinnacle Pack)",
    "Baro Void-Signal (Key)",
}
UNICODE_RANK_PATTERN = re.compile(r"[\uE000-\uF8FF]")

# ===================================== COPY =====================================


def copy(listing_to_copy: dict[str, Any], max_ranks: dict[str, int | None]) -> str:
    """Copy a listing for in-game whispering."""
    item_id = listing_to_copy["itemId"]
    item_name = listing_to_copy["item"]

    if listing_to_copy.get("rank") is not None:
        item_name = f"{item_name} (rank {listing_to_copy['rank']}/{max_ranks[item_id]})"

    segments = [
        "WTB",
        item_name,
        f"{listing_to_copy['price']}p",
    ]
    message = f"/w {listing_to_copy['seller']} {' | '.join(segments)}"

    pyperclip.copy(message)

    return message


# ==================================== SEARCH ====================================


async def search(
    item_slug: str,
    id_to_name: dict[str, str],
    max_ranks: dict[str, int | None],
    session: aiohttp.ClientSession,
    rank: int | None = None,
    sort: str = "price",
    order: str | None = None,
    status: str = "ingame",
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    item_listings = await extract_item_listings(session, item_slug, id_to_name)
    if not item_listings:
        return (False, "No listings available.", [])
    filtered_item_listings = filter_listings(item_listings, rank, status)
    if not filtered_item_listings:
        return (False, "No listings match specified filters.", [])
    sorted_item_listings, sort_order = sort_listings(
        filtered_item_listings, sort, order, DEFAULT_ORDERS
    )
    data_rows = build_search_rows(sorted_item_listings, max_ranks)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, sort_order)

    return (True, None, sorted_item_listings)


# =================================== LISTINGS ===================================


async def listings(
    id_to_name: dict[str, str],
    max_ranks: dict[str, int | None],
    user: str,
    headers: dict[str, str],
    session: aiohttp.ClientSession,
    rank: int | None = None,
    sort: str = "updated",
    order: str | None = None,
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    user_listings = await extract_user_listings(session, user, id_to_name, headers)
    if not user_listings:
        return (False, "No listings available.", [])
    filtered_user_listings = filter_listings(user_listings, rank, status="all")
    if not filtered_user_listings:
        return (False, "No listings match specified filters.", [])
    sorted_user_listings, sort_order = sort_listings(
        filtered_user_listings, sort, order, {**DEFAULT_ORDERS, "price": "desc"}
    )
    data_rows = build_listings_rows(sorted_user_listings, max_ranks)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, sort_order)

    return (True, None, sorted_user_listings)


# ==================================== SELLER ====================================


async def seller(
    id_to_name: dict[str, str],
    max_ranks: dict[str, int | None],
    slug: str,
    seller: str,
    session: aiohttp.ClientSession,
    rank: int | None = None,
    sort: str = "updated",
    order: str | None = None,
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    seller_listings = await extract_seller_listings(session, slug, seller, id_to_name)
    if not seller_listings:
        return (False, "No listings available.", [])
    filtered_seller_listings = filter_listings(seller_listings, rank, status="all")
    if not filtered_seller_listings:
        return (False, "No listings match specified filters.", [])
    sorted_seller_listings, sort_order = sort_listings(
        filtered_seller_listings, sort, order, DEFAULT_ORDERS
    )
    data_rows = build_seller_rows(sorted_seller_listings, max_ranks)
    column_widths = determine_widths(data_rows, sort)
    display_listings(data_rows, column_widths, RIGHT_ALLIGNED_COLUMNS, sort, sort_order)

    return (True, None, sorted_seller_listings)


# ==================================== LINKS =====================================


def _get_base_name(item_name: str) -> str:
    """Extract base name without part suffixes."""
    words = item_name.split()
    while words and words[-1] in PART_SUFFIXES:
        words.pop()

    return " ".join(words)


def _expand_item_sets(
    user_listings: list[dict[str, Any]], all_items: list[dict[str, Any]]
) -> list[str]:
    """Expand set items into individual parts for the set."""
    expanded_items = []

    for listing in user_listings:
        if listing["item"].endswith(" Set"):
            set_base = _get_base_name(listing["item"])
            for item in all_items:
                item_name = item["i18n"]["en"]["name"]
                item_base = _get_base_name(item_name)
                if set_base == item_base and item_name != listing["item"]:
                    expanded_items.append(item_name)
        else:
            expanded_items.append(listing["item"])

    return expanded_items


def _filter_unlinkable_items(items: list[str]) -> list[str]:
    filtered_items = [item for item in items if item not in UNLINKABLE_ITEMS]

    return filtered_items


def _convert_items_to_links(items: list[str]) -> list[str]:
    """Process and format item names for ingame pasting."""
    return [
        f"[{listing.replace(' Blueprint', '')}]"
        if "Blueprint" in listing
        else f"[{listing}]"
        for listing in items
    ]


def _chunk_links(links: list[str]) -> list[str]:
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


def _print_prep_status(total_items: int, skipped_items: int) -> None:
    link_count = total_items - skipped_items
    print(f"\nPrepared {link_count} links.")
    if skipped_items > 0:
        print(f"Skipped {skipped_items} unlinkable items.")


async def _copy_to_clipboard(chunks: list[str], prompt_session: PromptSession) -> None:
    for i, chunk in enumerate(chunks, 1):
        pyperclip.copy(chunk)
        if i < len(chunks):
            await prompt_session.prompt_async(
                f"\nChunk {i}/{len(chunks)} copied. Press Enter..."
            )
        else:
            print(f"\nChunk {i}/{len(chunks)} copied.\n")


async def links(
    all_items: list[dict[str, Any]],
    id_to_name: dict[str, str],
    user: str,
    headers: dict[str, str],
    session: aiohttp.ClientSession,
    prompt_session: PromptSession,
    sort: str = "item",
    order: str | None = None,
) -> tuple[bool, str | None]:
    user_listings = await extract_user_listings(session, user, id_to_name, headers)
    if not user_listings:
        return (False, "No listings available.")
    sorted_user_listings, _ = sort_listings(user_listings, sort, order, DEFAULT_ORDERS)
    expanded_items = _expand_item_sets(sorted_user_listings, all_items)
    filtered_items = _filter_unlinkable_items(expanded_items)
    links = _convert_items_to_links(filtered_items)
    link_chunks = _chunk_links(links)
    _print_prep_status(len(expanded_items), len(expanded_items) - len(filtered_items))
    await _copy_to_clipboard(link_chunks, prompt_session)

    return (True, None)


# ===================================== SYNC =====================================


def _get_log_path() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData/Local/Warframe/EE.log"
    elif sys.platform == "linux":
        # Check for WSL
        try:
            with Path("/proc/version").open("r") as f:
                if "microsoft" in f.read().lower():
                    username = (
                        subprocess.check_output(["whoami.exe"], text=True)
                        .strip()
                        .split("\\")[-1]
                    )
                    return (
                        Path("/mnt/c/Users")
                        / username
                        / "AppData/Local/Warframe/EE.log"
                    )
        except FileNotFoundError:
            pass
        # Native linux
        return (
            Path.home()
            / ".steam/steam/steamapps/compatdata/230410/pfx/drive_c/users/steamuser/AppData/Local/Warframe/EE.log"
        )
    else:
        raise RuntimeError(f"\nUnsupported platform: {sys.platform}\n")


def _extract_trade_chunks(lines: list[str]) -> list[list[str]]:
    trade_chunks = []
    current_chunk = []
    recording = False

    for line in lines:
        if "Are you sure you want to accept this trade?" in line:
            current_chunk = [line]
            recording = True

        elif "SendResult_MENU_CANCEL()" in line:
            current_chunk = []
            recording = False

        elif "The trade was successful!" in line and recording:
            current_chunk.append(line)
            trade_chunks.append(current_chunk)
            recording = False

        elif recording:
            current_chunk.append(line)

    return trade_chunks


def _parse_trade_items(
    trade_chunks: list[list[str]],
) -> list[dict[str, tuple[str, ...]]]:
    def normalize_item_name(raw_name: str) -> str:
        name = raw_name.split("(")[0].strip()
        name = re.sub(UNICODE_RANK_PATTERN, "", name).strip()
        return name

    parsed_trades = []
    for chunk in trade_chunks:
        offered_items = []
        received_items = []
        in_offer_section = False
        in_receive_section = False

        for line in chunk:
            if "offering" in line:
                in_offer_section = True
            elif "receive" in line:
                in_offer_section = False
                in_receive_section = True
            elif "Confirm_Item_Cancel" in line:
                received_items.append(line.split(",")[0])
                in_receive_section = False
            elif in_offer_section:
                offered_items.append(line)
            elif in_receive_section:
                received_items.append(line)

        parsed_trades.append(
            {
                "offered": tuple(
                    normalize_item_name(item) for item in offered_items if item
                ),
                "received": tuple(
                    normalize_item_name(item) for item in received_items if item
                ),
            }
        )

    return parsed_trades


def _load_sync_state() -> dict[str, int]:
    if not SYNC_STATE_FILE.exists():
        return {"last_byte_offset": 0}

    with SYNC_STATE_FILE.open("r") as f:
        return json.load(f)


def _save_sync_state(offset) -> None:
    with SYNC_STATE_FILE.open("w") as f:
        json.dump({"last_byte_offset": offset}, f)


def _get_log_lines(log_path: Path, state: dict[str, int]) -> tuple[list[str], int]:
    with log_path.open("rb") as f:
        file_size = log_path.stat().st_size

        if file_size < state["last_byte_offset"]:
            state["last_byte_offset"] = 0

        f.seek(state["last_byte_offset"])
        lines = f.read().decode("utf-8").splitlines()
        offset = f.tell()

    return lines, offset


async def _update_listings(
    id_to_tags: dict[str, set[str]],
    id_to_bulkTradable: dict[str, bool],
    listings: list[dict[str, Any]],
    trades: list[dict[str, tuple[str, ...]]],
    session: aiohttp.ClientSession,
    headers: dict[str, str],
) -> None:
    """Decrement quantities or delete listings based on trade patterns in EE.log"""
    sync_occurred = False
    for trade in trades:
        candidates = []
        for listing in listings:
            if listing["item"] in trade["offered"]:
                candidates.append(listing)

        if not candidates:
            continue

        sync_occurred = True

        print("\nSyncing listings...\n")

        plat_received = sum(
            int(item.split()[-1]) for item in trade["received"] if "Platinum" in item
        )

        item_count = trade["offered"].count(candidates[0]["item"])
        plat_per_item = plat_received // item_count
        candidate = min(
            candidates, key=lambda listing: abs(plat_per_item - listing["price"])
        )

        candidate["quantity"] -= item_count

        if candidate["quantity"] <= 0:
            await delete_listing(session, candidate["id"], headers)
            listings.remove(candidate)
            print(f"Deleted {candidate['item']} listing.")
        else:
            fields = ["price", "quantity", "rank", "visible"]
            kwargs = {
                field: candidate[field]
                for field in fields
                if candidate[field] is not None
            }
            await edit_listing(session, headers, candidate["id"], **kwargs)
            print(
                f"Updated {candidate['item']} listing quantity to {candidate['quantity']}."
            )

        await asyncio.sleep(0.5)  # Rate limit

    if not sync_occurred:
        print("\nNo listings synced.\n")


async def sync(
    id_to_name: dict[str, str],
    id_to_tags: dict[str, set[str]],
    id_to_bulkTradable: dict[str, bool],
    user: str,
    session: aiohttp.ClientSession,
    headers: dict[str, str],
) -> tuple[bool, str | None]:
    user_listings = await extract_user_listings(session, user, id_to_name, headers)
    if not user_listings:
        return (False, "No listings found.")
    log_path = _get_log_path()
    state = _load_sync_state()
    lines, offset = _get_log_lines(log_path, state)
    _save_sync_state(offset)
    trade_chunks = _extract_trade_chunks(lines)
    if not trade_chunks:
        return (False, "No trades found.")
    trades = _parse_trade_items(trade_chunks)
    await _update_listings(
        id_to_tags, id_to_bulkTradable, user_listings, trades, session, headers
    )

    return (True, None)
