COLUMNS = ["#", "wfm_cli"]

OPTIONS = [
    "Search for item",
    "Show my listings",
    "Update my listings",
    "Authenticate",
    "Profile",
    "Log out",
    "Quit",
]


def build_rows():
    """Build rows for table rendering."""
    return [
        {"#": str(i), "wfm_cli": option} for i, option in enumerate(OPTIONS, start=1)
    ]


def determine_width(data_rows):
    """Determine maximum width for each colunm."""
    column_widths = {col: 0 for col in COLUMNS}
    for row in data_rows:
        for col in COLUMNS:
            column_widths[col] = max(
                column_widths[col],
                len(str(row.get(col, ""))),
                len(col),
            )

    # Account for spacing
    column_widths = {key: width + 2 for key, width in column_widths.items()}

    return column_widths


def display_menu(data_rows, column_widths):
    """Display menu in a sql-like table."""

    separator_row = ["-" * width for width in column_widths.values()]

    header_row = [key.center(width) for key, width in column_widths.items()]

    print(f"+{'+'.join(separator_row)}+")
    print(f"|{'|'.join(header_row)}|")
    print(f"+{'+'.join(separator_row)}+")

    for row in data_rows:
        data_row = []
        for key in column_widths:
            value = row.get(key, "")

            formatted = f" {value}".ljust(column_widths[key])

            data_row.append(formatted)

        print(f"|{'|'.join(data_row)}|")

    print(f"+{'+'.join(separator_row)}+")


def menu():
    data_rows = build_rows()
    column_widths = determine_width(data_rows)
    display_menu(data_rows, column_widths)
