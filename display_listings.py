from utils import (
    build_id_to_name_mapping,
    extract_user_listings,
    get_all_items,
)


def format_listings(listings):
    data_rows = []
    for item, details in listings.items():
        row = {
            "item": item,
            "price": str(details["price"]),
            "rank": str(details["rank"]) if details["rank"] is not None else "N/A",
            "quantity": str(details["quantity"]),
        }
        data_rows.append(row)

    # Determine column widths
    column_widths = {"item": 0, "price": 0, "rank": 0, "quantity": 0}
    for row in data_rows:
        for key in row:
            column_widths[key] = max(column_widths[key], len(row[key]), len(key))

    # Account for spacing
    for key in column_widths:
        column_widths[key] += 2

    header_row = [
        key.title().center((value), " ") for key, value in column_widths.items()
    ]

    print(f"|{'|'.join(header_row)}|")

    for row in data_rows:
        data_row = [row[key].ljust(column_widths[key]) for key in row]

        print(f"|{'|'.join(data_row)}|")


def display_listings():
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    user_listings = extract_user_listings("bhwsg", id_to_name)
    format_listings(user_listings)


if __name__ == "__main__":
    display_listings()
