from typing import Any


def parse_search_args(args: list[str]) -> tuple[str, dict[str, Any]]:
    item = args[0]

    kwargs = {
        "sort": "price",
        "order": None,
        "rank": None,
        "status": "ingame",
    }

    rest = args[1:]
    pairs = zip(rest[::2], rest[1::2])

    for key, value in pairs:
        kwargs[key] = value

    if kwargs["rank"]:
        kwargs["rank"] = int(kwargs["rank"])

    return item, kwargs


def parse_listings_args(args: list[str]) -> dict[str, Any]:
    kwargs = {
        "sort": "updated",
        "order": None,
        "rank": None,
    }

    pairs = zip(args[::2], args[1::2])

    for key, value in pairs:
        kwargs[key] = value

    if kwargs["rank"]:
        kwargs["rank"] = int(kwargs["rank"])

    return kwargs


def parse_add_args(args: list[str]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"item_name": args[0]}
    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        kwargs[key] = int(value)

    return kwargs


def parse_seller_args(args: list[str]) -> dict[str, Any]:
    kwargs = {}
    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        kwargs[key] = value

    return kwargs


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
