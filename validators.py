from typing import Any


def validate_add_args(
    kwargs: dict[str, Any],
    name_to_id: dict[str, str],
    id_to_name: dict[str, str],
    id_to_max_rank: dict[str, int | None],
    id_to_tags: dict[str, set[str]],
    id_to_bulkTradable: dict[str, bool],
) -> tuple[bool, str | None]:
    if "item_name" not in kwargs:
        return (False, "No item specified.")
    elif kwargs["item_name"] not in name_to_id:
        return (False, f"'{kwargs['item_name']}' is not a valid item.")

    kwargs["item_id"] = name_to_id[kwargs["item_name"]]
    del kwargs["item_name"]

    item_id = kwargs["item_id"]

    item_name = id_to_name[item_id]
    max_rank: int | None = id_to_max_rank[item_id]
    item_tags = id_to_tags[item_id]
    is_bulk_tradeable = id_to_bulkTradable[item_id]

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
            return (False, f"No ranks for{item_name}.")
        if rank < 0 or rank > max_rank:
            return (False, f"Invalid rank (0-{max_rank}).")

    return (True, None)


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
