from typing import Any

# ==================================== UTILS =====================================


def check_invalid_fields(
    kwargs: dict[str, Any], allowed: set[str]
) -> tuple[bool, str | None]:
    """Check for fields not in the allowed set."""
    invalid = [key for key in kwargs if key not in allowed]

    if not invalid:
        return (True, None)

    return (
        False,
        f"'{invalid[0]}' is not a valid field."
        if len(invalid) == 1
        else f"{', '.join(f"'{k}'" for k in invalid[:-1])} and '{invalid[-1]}' are not valid fields.",
    )


def convert_to_int(
    kwargs: dict[str, Any], fields: list[str]
) -> tuple[bool, str | None]:
    """Convert specified fields to integers."""
    non_numeric = []
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            try:
                kwargs[field] = int(kwargs[field])
            except (ValueError, TypeError):
                non_numeric.append(field)

    if not non_numeric:
        return (True, None)

    return (
        False,
        f"{non_numeric[0].capitalize()} must be a number."
        if len(non_numeric) == 1
        else f"{', '.join(non_numeric[:-1])} and {non_numeric[-1]} must be numbers.".capitalize(),
    )


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


def _check_missing_fields(
    kwargs: dict[str, Any], required: list[str]
) -> tuple[bool, str | None]:
    """Check for fields not in the required list."""
    missing = [field for field in required if field not in kwargs]

    if not missing:
        return (True, None)

    return (
        False,
        f"No {missing[0]} specified."
        if len(missing) == 1
        else f"No {', '.join(missing[:-1])} or {missing[-1]} specified.",
    )


def validate_add_args(
    kwargs: dict[str, Any],
    name_to_id: dict[str, str],
    id_to_name: dict[str, str],
    id_to_max_rank: dict[str, int | None],
    id_to_tags: dict[str, set[str]],
    id_to_bulk_tradable: dict[str, bool],
) -> tuple[bool, str | None]:
    # Validate input fields
    success, error = check_invalid_fields(
        kwargs, {"item_name", "price", "quantity", "rank"}
    )
    if not success:
        return (False, error)

    # Check item name
    if "item_name" not in kwargs:
        return (False, "No item specified.")
    elif kwargs["item_name"] not in name_to_id:
        return (False, f"'{kwargs['item_name']}' is not a valid item.")

    # Transform item_name into item_id
    kwargs["item_id"] = name_to_id[kwargs["item_name"]]
    del kwargs["item_name"]

    item_id = kwargs["item_id"]
    item_name = id_to_name[item_id]
    max_rank = id_to_max_rank[item_id]
    item_tags = id_to_tags[item_id]
    is_bulk_tradeable = id_to_bulk_tradable[item_id]

    if "arcane_enhancement" in item_tags and is_bulk_tradeable:
        kwargs["per_trade"] = 1

    # Check for missing required fields
    required = ["price", "quantity"]
    if max_rank is not None:
        required.append("rank")
    success, error = _check_missing_fields(kwargs, required)
    if not success:
        return (False, error)

    # Convert numeric fields
    success, error = convert_to_int(kwargs, ["price", "quantity", "rank"])
    if not success:
        return (False, error)

    # Validate rank if present
    if "rank" in kwargs:
        kwargs["rank"] = kwargs["rank"]
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
    # Validate input fields
    success, error = check_invalid_fields(
        kwargs, {"item_name", "price", "quantity", "rank"}
    )
    if not success:
        return (False, error)

    item_name = id_to_name[item_id]
    max_rank = id_to_max_rank[item_id]
    item_tags = id_to_tags[item_id]
    is_bulk_tradeable = id_to_bulk_tradable[item_id]

    if "arcane_enhancement" in item_tags and is_bulk_tradeable:
        kwargs["per_trade"] = 1

    # Convert numeric fields
    success, error = convert_to_int(kwargs, ["price", "quantity", "rank"])
    if not success:
        return (False, error)

    if "rank" in kwargs:
        kwargs["rank"] = int(kwargs["rank"])
        rank = kwargs["rank"]
        if max_rank is None:
            return (False, f"No ranks for {item_name}.")
        if rank < 0 or rank > max_rank:
            return (False, f"Invalid rank for {item_name} (0-{max_rank}).")

    return (True, None)
