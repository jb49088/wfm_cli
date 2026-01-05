from utils import (
    build_id_to_name_mapping,
    extract_user_listings,
    get_all_items,
)


def format_listings(listings):
    rows = []
    for name, details in listings.items():
        row = {
            "name": name,
            "price": str(details["price"]),
            "quantity": str(details["quantity"]),
            "rank": str(details["rank"]) if details["rank"] is not None else "N/A",
        }
        rows.append(row)

    max_widths = {"name": 0, "price": 0, "quantity": 0, "rank": 0}
    for row in rows:
        max_widths["name"] = max(max_widths["name"], len(row["name"]))
        max_widths["price"] = max(max_widths["price"], len(row["price"]))
        max_widths["rank"] = max(max_widths["rank"], len(row["rank"]))
        max_widths["quantity"] = max(max_widths["quantity"], len(row["quantity"]))

    for row in rows:
        message = f"| {row['name']}{' ' * (max_widths['name'] - len(row['name']))} | Price: {row['price']}p{' ' * (max_widths['price'] - len(row['price']))} | Rank: {row['rank']}{' ' * (max_widths['rank'] - len(row['rank']))} | Quantity: {row['quantity']}{' ' * (max_widths['quantity'] - len(row['quantity']))} |"
        print(message)


def display_listings():
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    user_listings = extract_user_listings("bhwsg", id_to_name)
    format_listings(user_listings)


if __name__ == "__main__":
    display_listings()
