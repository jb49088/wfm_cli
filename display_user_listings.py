import pyperclip

from utils import (
    build_id_to_name_mapping,
    extract_user_listings,
    get_all_items,
    sort_user_listings,
)


def build_rows(listings, copy=True):
    """Build rows for table rendering."""
    data_rows = []
    for i, listing in enumerate(listings, start=1):
        row = {
            "#": str(i),
            "item": listing["item"],
            "price": str(listing["price"]),
            "rank": str(listing["rank"]) if listing["rank"] is not None else "",
            "quantity": str(listing["quantity"]),
            "updated": str(listing["updated"]),
            "created": str(listing["created"]),
        }
        if not copy:
            del row["#"]
        data_rows.append(row)

    return data_rows


def determine_widths(data_rows, sort_by):
    """Determine maximum width for each colunm."""
    column_widths = {key: 0 for key in data_rows[0]}

    for row in data_rows:
        for key in row:
            column_widths[key] = max(
                column_widths[key],
                len(row[key]) + 1 if key == "price" else len(row[key]),  # +1 for p
                len(key) + 2 if key == sort_by else len(key),  # +2 for arrow
            )

    # Account for spacing
    column_widths = {key: width + 2 for key, width in column_widths.items()}

    return column_widths


def display_listings(data_rows, column_widths, sort_by, order):
    """Display listings in a sql-like table."""
    separator_row = ["-" * width for width in column_widths.values()]

    arrows = {"desc": "↓", "asc": "↑"}

    header_row = [
        f"{key} {arrows[order]}".title().center(width)
        if key == sort_by
        else key.title().center(width)
        for key, width in column_widths.items()
    ]

    print(f"+{'+'.join(separator_row)}+")
    print(f"|{'|'.join(header_row)}|")
    print(f"+{'+'.join(separator_row)}+")

    for row in data_rows:
        data_row = [
            f" {value}p".ljust(column_widths[key])
            if key == "price"
            else f" {value}".ljust(column_widths[key])
            for key, value in row.items()
        ]

        print(f"|{'|'.join(data_row)}|")

    print(f"+{'+'.join(separator_row)}+")


def copy_listing(user, data_rows):
    listing = input("Listing to copy: ").strip()

    for row in data_rows:
        if row["#"] == listing:
            rank_segment = f" (rank {row['rank']})" if row["rank"] else ""
            message = f'/w {user} Hi! I want to buy: "{row["item"]}{rank_segment}" for {row["price"]} platinum. (wfm_cli)'
            pyperclip.copy(message)
            print(f"Copied to clipboard: {message}")
            return

    print(f"Listing {listing} not found")


def display_user_listings():
    """Main entry point."""
    args = {
        "user": "bhwsg",
        "copy": True,
    }
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    user_listings = extract_user_listings(args["user"], id_to_name)
    sorted_user_listings, sort_by, order = sort_user_listings(user_listings)
    data_rows = build_rows(sorted_user_listings, args["copy"])
    column_widths = determine_widths(data_rows, sort_by)
    display_listings(data_rows, column_widths, sort_by, order)
    if args["copy"]:
        copy_listing(args["user"], data_rows)


if __name__ == "__main__":
    display_user_listings()
