# ================================================================================
# =                                   WFM_CLI                                    =
# ================================================================================

import shlex

from prompt_toolkit import prompt

from copy_user_listings import copy_user_listings
from display_item_listings import display_item_listings
from display_user_listings import display_user_listings
from utils import clear_screen


def wfm_cli():
    while True:
        try:
            cmd = prompt("wfm_cli> ").strip()
        except KeyboardInterrupt:
            break

        parts = shlex.split(cmd)
        action = parts[0].lower()
        args = parts[1:]

        if action == "search":
            item = args[0]

            kwargs = {
                "sort": "price",
                "order": None,
                "rank": None,
                "status": "ingame",
            }

            rest = args[1:]
            pairs = zip(rest[::2], rest[1::2])

            for key, value in pairs:
                kwargs[key] = value

            if kwargs["rank"]:
                kwargs["rank"] = int(kwargs["rank"])

            display_item_listings(item=item, **kwargs)

        elif action == "clear":
            clear_screen()


if __name__ == "__main__":
    try:
        wfm_cli()
    except KeyboardInterrupt:
        pass
