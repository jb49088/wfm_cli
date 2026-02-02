from typing import Any

# ==================================== SEARCH ====================================


def validate_search_args(kwargs: dict[str, Any]) -> tuple[bool, str | None]:
    valid_sorts = [
        "seller",
        "reputation",
        "status",
        "item",
        "price",
        "rank",
        "quantity",
        "updated",
    ]
    valid_orders = ["asc", "desc"]
    if "rank" in kwargs:
        try:
            kwargs["rank"] = int(kwargs["rank"])
        except ValueError:
            return (False, "Rank must be a number.")

    if "sort" in kwargs and kwargs["sort"] not in valid_sorts:
        return (False, "Invalid sort.")

    if "order" in kwargs and kwargs["order"] not in valid_orders:
        return (False, "Invalid order.")

    return (True, None)


# =================================== LISTINGS ===================================


def validate_listings_args(kwargs: dict[str, Any]) -> tuple[bool, str | None]:
    if "rank" in kwargs:
        try:
            kwargs["rank"] = int(kwargs["rank"])
        except ValueError:
            return (False, "Rank must be a number.")

    return (True, None)


# ==================================== SELLER ====================================


def validate_seller_listing_selection(
    args: list[str], current_listings: list[dict[str, Any]]
) -> tuple[bool, str | None, dict[str, Any] | None]:
    if not args or not args[0].isdigit():
        return (False, "No listing specified.", None)

    if not current_listings:
        return (False, "No listings available.", None)

    index = int(args[0]) - 1

    if not (0 <= index < len(current_listings)):
        return (False, "Invalid listing number.", None)

    listing = current_listings[index]

    if "id" in current_listings[index]:
        return (False, "Cannot view own listings with this command.", None)

    if "reputation" not in current_listings[index]:
        return (False, "Already viewing a seller.", None)

    return (True, None, listing)


def validate_seller_args(kwargs: dict[str, Any]) -> tuple[bool, str | None]:
    valid_sorts = ["item", "price", "rank", "quantity", "updated"]
    valid_orders = ["asc", "desc"]

    if "rank" in kwargs:
        try:
            kwargs["rank"] = int(kwargs["rank"])
        except ValueError:
            return (False, "Rank must be a number.")

    if "sort" in kwargs and kwargs["sort"] not in valid_sorts:
        return (False, "Invalid sort.")

    if "order" in kwargs and kwargs["order"] not in valid_orders:
        return (False, "Invalid order.")

    return (True, None)


# ===================================== ADD ======================================


def validate_add_args(
    kwargs: dict[str, Any],
    name_to_id: dict[str, str],
    id_to_name: dict[str, str],
    id_to_max_rank: dict[str, int | None],
    id_to_tags: dict[str, set[str]],
    id_to_bulk_tradable: dict[str, bool],
) -> tuple[bool, str | None]:
    if "item_name" not in kwargs:
        return (False, "No item specified.")
    elif kwargs["item_name"] not in name_to_id:
        return (False, f"'{kwargs['item_name']}' is not a valid item.")

    kwargs["item_id"] = name_to_id[kwargs["item_name"]]
    del kwargs["item_name"]

    item_id = kwargs["item_id"]

    item_name = id_to_name[item_id]
    max_rank = id_to_max_rank[item_id]
    item_tags = id_to_tags[item_id]
    is_bulk_tradeable = id_to_bulk_tradable[item_id]

    if "arcane_enhancement" in item_tags and is_bulk_tradeable:
        kwargs["per_trade"] = 1

    missing = []
    if "price" not in kwargs:
        missing.append("price")
    if "quantity" not in kwargs:
        missing.append("quantity")
    if max_rank is not None and "rank" not in kwargs:
        missing.append("rank")

    if missing:
        return (
            False,
            f"No {missing[0]} specified"
            if len(missing) == 1
            else f"No {', '.join(missing[:-1])} or {missing[-1]} specified.",
        )

    if "rank" in kwargs:
        rank = kwargs["rank"]
        if max_rank is None:
            return (False, f"No ranks for {item_name}.")
        if rank < 0 or rank > max_rank:
            return (False, f"Invalid rank for {item_name} (0-{max_rank}).")

    return (True, None)


# ===================================== EDIT =====================================


def validate_edit_args(
    kwargs: dict[str, Any],
    item_id: str,
    id_to_name: dict[str, str],
    id_to_max_rank: dict[str, int | None],
    id_to_tags: dict[str, set[str]],
    id_to_bulk_tradable: dict[str, bool],
) -> tuple[bool, str | None]:
    item_name = id_to_name[item_id]
    max_rank = id_to_max_rank[item_id]
    item_tags = id_to_tags[item_id]
    is_bulk_tradeable = id_to_bulk_tradable[item_id]

    if "arcane_enhancement" in item_tags and is_bulk_tradeable:
        kwargs["per_trade"] = 1

    for field in ["price", "quantity", "rank"]:
        if field in kwargs and kwargs[field] is not None:
            try:
                kwargs[field] = int(kwargs[field])
            except ValueError:
                return (False, f"{field.capitalize()} must be a number.")

    if "rank" in kwargs:
        rank = kwargs["rank"]
        if max_rank is None:
            return (False, f"No ranks for {item_name}.")
        if rank < 0 or rank > max_rank:
            return (False, f"Invalid rank for {item_name} (0-{max_rank}).")

    return (True, None)
