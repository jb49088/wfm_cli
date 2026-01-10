# ================================================================================
# =                                   WFM_CLI                                    =
# ================================================================================

# TODO: Reverse engineer username normalization for api url
# TODO: Reverse engineer item names normalization for api url
# TODO: Add secondary sort by updated to break price ties
# TODO: Add error handling when a user has 0 listings
# TODO: Deal with ayatan sculpture ranking
# TODO: Add ranking API query

import argparse

from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    item_parser = subparsers.add_parser("item", help="Display item listings")
    item_parser.add_argument("item", help="Name of the item")
    item_parser.add_argument("--sort", default="price", help="Field to sort by")
    item_parser.add_argument("--order", default=None, help="Sort order")
    item_parser.add_argument(
        "--no-in-game",
        action="store_false",
        dest="in_game",
        help="Include offline sellers",
    )
    item_parser.add_argument(
        "--no-copy",
        action="store_false",
        dest="copy",
        help="Skip copy prompt",
    )
    item_parser.set_defaults(func=display_item_listings)

    user_parser = subparsers.add_parser("user", help="Display user listings")
    user_parser.add_argument("user", help="In game username")
    user_parser.add_argument("--sort", default="updated", help="Field to sort by")
    user_parser.add_argument("--order", default=None, help="Sort order")
    user_parser.add_argument(
        "--copy",
        action="store_true",
        help="Enable copy prompt",
    )
    user_parser.set_defaults(func=display_user_listings)

    copy_parser = subparsers.add_parser("copy", help="Copy user listings")
    copy_parser.add_argument("user", help="In game username")
    copy_parser.add_argument("--sort", default="updated", help="Field to sort by")
    copy_parser.add_argument("--order", default=None, help="Sort order")

    copy_parser.set_defaults(func=copy_user_listings)

    args = parser.parse_args()
    args.func(args)
