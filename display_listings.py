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

    # Determine column widths
    column_widths = {"name": 0, "price": 0, "quantity": 0, "rank": 0}
    for row in rows:
        for key in row:
            column_widths[key] = max(column_widths[key], len(row[key]), len(key))

    # Account for spacing
    for key in column_widths:
        column_widths[key] += 2

    print(
        f"|{'Item'.center(column_widths['name'], ' ')}|{'Price'.center(column_widths['price'], ' ')}|{'Rank'.center(column_widths['rank'], ' ')}|"
    )

    for row in rows:
        message = f"|{row['name']}{' ' * (column_widths['name'] - len(row['name']))}|{row['price']}{' ' * (column_widths['price'] - len(row['price']))}|{row['rank']}{' ' * (column_widths['rank'] - len(row['rank']))}|{row['quantity']}{' ' * (column_widths['quantity'] - len(row['quantity']))}|"
        print(message)


def display_listings():
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    user_listings = extract_user_listings("bhwsg", id_to_name)
    format_listings(user_listings)


if __name__ == "__main__":
    display_listings()
