from __future__ import annotations
import time
import sys
import json
import logging
from typing import List
import os

import discord
import requests

from src.consts import OPENSEA_EVENTS_URL, SLEEP_TIME, ONE_HOUR_IN_SECONDS
from src.sales_bot import SalesBotType, SalesBot
from src.util import handle_exception
from src.opensea import SalesDatum
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def run(sales_bot_type: SalesBotType = SalesBotType.KONG):
    this_path = os.path.dirname(os.path.abspath(__file__))
    since_path = os.path.join(this_path, "sales_since", f"{sales_bot_type.value}.json")

    since_index = json.loads(open(since_path).read())["index"]
    since_block = json.loads(open(since_path).read())["block"]
    since_timestamp = json.loads(open(since_path).read())["timestamp"]

    def update_since(data: List[SalesDatum]):
        nonlocal since_index, since_block

        since_index = data[0].transaction_index
        since_block = data[0].transaction_block

        with open(since_path, "w") as f:
            f.write(
                json.dumps(
                    {
                        "index": since_index,
                        "block": since_block,
                        "timestamp": int(time.time()),
                    }
                )
            )

    print("Creating sales bot...")

    sales_bot = SalesBot(sales_bot_type)

    print(f"Preparing webhook {sales_bot.discord_webhook}")

    webhook = discord.Webhook.from_url(
        sales_bot.discord_webhook, adapter=discord.RequestsWebhookAdapter()
    )

    print("Fetching sales data...")
    response = requests.request(
        "GET",
        OPENSEA_EVENTS_URL
        + sales_bot.opensea_slug
        + f"?after={since_timestamp}&event_type=sale",
        headers={
            "accept": "application/json",
            "x-api-key": os.getenv("OPENSEA_API_KEY"),
        },
    )

    response_json = response.json()

    # * we need to go from oldest sales to newest ones here
    sales_data = response_json["asset_events"]

    print(
        f"Found {len(sales_data)} sales since {datetime.utcfromtimestamp(since_timestamp).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    for sales_datum in sales_data:
        data: List[SalesDatum] = SalesDatum.from_json(sales_datum)

        discord_messages = sales_bot.build_discord_messages(data)
        for msg in discord_messages:
            webhook.send(embed=msg)

        # ! note that we might send a discord message but not a twitter message
        # ! the next run, we will send the same discord message again
        # ! one potential solution is keep re-trying sending a tweet
        # ! until it succeeds. Note that there is no problem if we fail
        # ! to send a discord message, we will just retry the whole thing
        # ! on the next run.
        update_since(data)


def main(bot_type: int):
    while True:
        run(SalesBotType.from_int(bot_type))
        logging.info("Sleeping for 10 minutes...")
        time.sleep(10 * SLEEP_TIME)


if __name__ == "__main__":
    try:
        bot_kind = int(sys.argv[1])

        suffix = ""
        if bot_kind == SalesBotType.KONG.value:
            suffix = "_kongs.log"
        elif bot_kind == SalesBotType.SNEAKER.value:
            suffix = "_sneakers.log"
        elif bot_kind == SalesBotType.ROOKIE.value:
            suffix = "_rookies.log"
        else:
            raise Exception("Invalid bot type")

        logging.basicConfig(
            filename="salesbot" + suffix,
            level=logging.INFO,
            format=(
                "%(process)d |:| %(levelname)s |:| %(asctime)s.%(msecs)03d |:| %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        main(int(sys.argv[1]))
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt caught. Gracefully exiting.")
        sys.exit(0)
    except:
        handle_exception()

        logging.warning("Error occured... Sleeping for 1 hour...")
        time.sleep(ONE_HOUR_IN_SECONDS)
        # re-running on error is handled by the OS
        # there is a file in this dir: `run.sh`
        # that you should run, instead of running
        # this file directly.
        sys.exit(1)
