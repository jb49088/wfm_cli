from utils import (
    build_id_to_name_mapping,
    extract_user_listings,
    get_all_items,
)


def format_listings(listings):
    longest_name = 0
    longest_price = 0
    longest_quantity = 0
    longest_rank = 0

    for listing in listings:
        price = str(listings[listing]["price"])
        quantity = str(listings[listing]["quantity"])

        if listings[listing]["rank"] is not None:
            rank = str(listings[listing]["rank"])
        else:
            rank = "N/A"

        if len(listing) > longest_name:
            longest_name = len(listing)

        if len(price) > longest_price:
            longest_price = len(price)

        if len(rank) > longest_rank:
            longest_rank = len(rank)

        if len(quantity) > longest_quantity:
            longest_quantity = len(quantity)

    for listing in sorted(listings):
        price = str(listings[listing]["price"])
        quantity = str(listings[listing]["quantity"])

        if listings[listing]["rank"] is not None:
            rank = str(listings[listing]["rank"])
        else:
            rank = "N/A"

        message = f"| {listing}{' ' * (longest_name - len(listing))} | Price: {price}p{' ' * (longest_price - len(price))} | Rank: {rank}{' ' * (longest_rank - len(rank))} | Quantity: {quantity}{' ' * (longest_quantity - len(quantity))} |"

        print(message)


def display_listings():
    all_items = get_all_items()
    id_to_name = build_id_to_name_mapping(all_items)
    user_listings = extract_user_listings("bhwsg", id_to_name)
    format_listings(user_listings)


if __name__ == "__main__":
    display_listings()
