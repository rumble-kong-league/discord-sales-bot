import time
import sys
import json
import logging
from typing import List
import os

import discord
import requests
import tweepy

from src.opensea import SalesDatum
import src.consts
from src.sales_bot import SalesBotType, SalesBot, is_fresh_sale
from src.util import handle_exception


def run(sales_bot_type: SalesBotType = SalesBotType.KONG):

    this_path = os.path.dirname(os.path.abspath(__file__))
    since_path = os.path.join(this_path, "sales_since", f"{sales_bot_type}.json")

    since_index = json.loads(open(since_path).read())["index"]
    since_block = json.loads(open(since_path).read())["block"]

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
                    }
                )
            )

    sales_bot = SalesBot(sales_bot_type)

    # twitter and discord authentication
    webhook = discord.Webhook.from_url(
        sales_bot.discord_webhook, adapter=discord.RequestsWebhookAdapter()
    )
    auth = tweepy.OAuthHandler(src.consts.TWEEPY_API_KEY, src.consts.TWEEPY_API_SECRET)
    auth.set_access_token(
        src.consts.TWEEPY_ACCESS_TOKEN, src.consts.TWEEPY_ACCESS_TOKEN_SECRET
    )
    api = tweepy.API(auth, wait_on_rate_limit=True)
    api.verify_credentials()

    # ! limit: "50" becomes a problem when we sell more than 50 kongs
    # ! in the timeframe that `main` function sleeps
    querystring = {
        "asset_contract_address": sales_bot.asset_contract_address,
        "event_type": "successful",
        "only_opensea": "false",
        "limit": "50",
    }

    response = requests.request(
        "GET",
        src.consts.OPENSEA_EVENTS_URL,
        headers=src.consts.HEADERS,
        params=querystring,
    )
    response_json = response.json()
    # * we need to go from oldest sales to newest ones here
    sales_data = response_json["asset_events"][::-1]

    for sales_datum in sales_data:

        data: List["SalesDatum"] = SalesDatum.from_json(sales_datum)

        # ! only interested in the latest trade
        fresh_sale = is_fresh_sale(data[0], since_block, since_index)
        if not fresh_sale:
            continue

        discord_messages = sales_bot.build_discord_messages(data)
        for msg in discord_messages:
            webhook.send(embed=msg)

        twitter_message = sales_bot.build_twitter_message(data)
        api.update_status(twitter_message)

        # ! note that we might send a discord message but not a twitter message
        # ! the next run, we will send the same discord message again
        # ! one potential solution is keep re-trying sending a tweet
        # ! until it succeeds. Note that there is no problem if we fail
        # ! to send a discord message, we will just retry the whole thing
        # ! on the next run.
        update_since(data)


def main(bot_type: int):

    while True:
        run(bot_type)
        logging.info("Sleeping for 10 minutes...")
        time.sleep(10 * src.consts.SLEEP_TIME)


if __name__ == "__main__":
    try:
        bot_kind = int(sys.argv[1])
        suffix = "_kongs.log" if bot_kind == SalesBotType.KONG else "_sneakers.log"
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
        time.sleep(src.consts.ONE_HOUR_IN_SECONDS)
        # re-running on error is handled by the OS
        # there is a file in this dir: `run.sh`
        # that you should run, instead of running
        # this file directly.
        sys.exit(1)
