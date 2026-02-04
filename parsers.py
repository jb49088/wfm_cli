from typing import Any

# =================================== GENERAL ====================================


def parse_args(args: list[str]) -> dict[str, Any]:
    kwargs = {}
    pairs = zip(args[::2], args[1::2])

    for key, value in pairs:
        kwargs[key] = value

    return kwargs


# ==================================== SEARCH ====================================


def parse_search_args(args: list[str]) -> tuple[str, dict[str, Any]]:
    kwargs = {}
    item = args[0]
    rest = args[1:]
    pairs = zip(rest[::2], rest[1::2])

    for key, value in pairs:
        kwargs[key] = value

    return item, kwargs


# ===================================== ADD ======================================


def parse_add_args(args: list[str]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"item_name": args[0]}
    pairs = zip(args[1::2], args[2::2])

    for key, value in pairs:
        kwargs[key] = value

    return kwargs
