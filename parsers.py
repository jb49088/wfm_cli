from typing import Any

# ==================================== SEARCH ====================================


def parse_search_args(args: list[str]) -> tuple[str, dict[str, Any]]:
    kwargs = {}
    item = args[0]
    rest = args[1:]
    pairs = zip(rest[::2], rest[1::2])

    for key, value in pairs:
        kwargs[key] = value

    return item, kwargs


# =================================== LISTINGS ===================================


def parse_listings_args(args: list[str]) -> dict[str, Any]:
    kwargs = {}
    pairs = zip(args[::2], args[1::2])

    for key, value in pairs:
        kwargs[key] = value

    return kwargs


# ===================================== ADD ======================================


def parse_add_args(args: list[str]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"item_name": args[0]}
    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        kwargs[key] = int(value)

    return kwargs


# ==================================== SELLER ====================================


def parse_seller_args(args: list[str]) -> dict[str, Any]:
    kwargs = {}
    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        kwargs[key] = value

    return kwargs


# ===================================== EDIT =====================================


def parse_edit_args(args: list[str], listing: dict[str, Any]) -> dict[str, Any]:
    kwargs = {
        "price": listing["price"],
        "quantity": listing["quantity"],
        "rank": listing["rank"],
        "visible": listing["visible"],
    }

    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        if key != "visible":
            value = int(value)
        kwargs[key] = value

    return kwargs
