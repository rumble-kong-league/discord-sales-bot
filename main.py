from typing import Dict, Union
from datetime import datetime, timedelta
import time
from enum import Enum, unique
import sys
import discord
import requests
import tweepy

from opensea import SalesDatum
from kongs import build_kong_discord_message, build_kong_twitter_message
from sneakers import build_sneaker_discord_message, build_sneaker_twitter_message
import consts


@unique
class SalesBotType(Enum):
    KONG = 0
    SNEAKER = 1

    @classmethod
    def from_int(cls, v: int) -> "SalesBotType":
        """
        Returns a corresponding enum for an int.

        Args:
            v (int): int to convert to enum.

        Raises:
            ValueError: If an unsupported int val is supplied.

        Returns:
            SalesBotType: corresponding enum.
        """
        if v == 0:
            return cls.KONG
        # elif v == 1:
        return cls.SNEAKER
        # raise ValueError(f'Cannot instantiate from {v}')


class SalesBot:
    def __init__(self, sales_bot_type: Union[SalesBotType, int]):

        if isinstance(sales_bot_type, int):
            self.sales_bot_type = SalesBotType.from_int(sales_bot_type)
        # ! note that this else contains all NON int types
        # ! ideally this branch only deals with SalesBotType
        else:
            self.sales_bot_type = sales_bot_type

        if self.sales_bot_type == SalesBotType.KONG:
            self.discord_webhook = consts.DISCORD_KONG_WEBHOOK
            self.asset_contract_address = consts.KONG_CONTRACT_ADDRESS
        elif self.sales_bot_type == SalesBotType.SNEAKER:
            self.discord_webhook = consts.DISCORD_SNEAKER_WEBHOOK
            self.asset_contract_address = consts.SNEAKER_CONTRACT_ADDRESS
        else:
            raise ValueError("Invalid sales_bot_type.")

    def build_discord_message(self, data: Dict) -> discord.Embed:
        """
        Builds discord message.

        Args:
            data (Dict): Opensea event data.

        Returns:
            discord.Embed: discord embed message.
        """

        if self.sales_bot_type == SalesBotType.KONG:
            return build_kong_discord_message(data)
        # elif self.sales_bot_type == SalesBotType.SNEAKER:
        return build_sneaker_discord_message(data)

    def build_twitter_message(self, data: Dict) -> str:
        """
        Builds twitter message.

        Args:
            data (Dict): Opensea event data.

        Returns:
            str: twitter message
        """

        if self.sales_bot_type == SalesBotType.KONG:
            return build_kong_twitter_message(data)
        # elif self.sales_bot_type == SalesBotType.SNEAKER:
        return build_sneaker_twitter_message(data)


def main(sales_bot_type: SalesBotType = SalesBotType.KONG):
    """
    If any sales happen, this will push a message to a Discord channel with details.
    This will also use tweepy to post a message on Twitter.
    """

    sales_bot = SalesBot(sales_bot_type)

    # twitter and discord authentication
    webhook = discord.Webhook.from_url(
        sales_bot.discord_webhook, adapter=discord.RequestsWebhookAdapter()
    )
    auth = tweepy.OAuthHandler(consts.TWEEPY_API_KEY, consts.TWEEPY_API_SECRET)
    auth.set_access_token(consts.TWEEPY_ACCESS_TOKEN, consts.TWEEPY_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    api.verify_credentials()

    since_time = datetime.utcnow() - timedelta(seconds=consts.SLEEP_TIME - 1)

    querystring = {
        "asset_contract_address": sales_bot.asset_contract_address,
        "event_type": "successful",
        "only_opensea": "false",
        "occurred_after": str(since_time).replace(" ", "T"),
        "offset": 0,
        "limit": "50",
    }

    response = requests.request(
        "GET", consts.OPENSEA_EVENTS_URL, headers=consts.HEADERS, params=querystring
    )
    response_json = response.json()
    sales_data = response_json["asset_events"]

    for sales_datum in sales_data:

        # build sales data from json
        data = SalesDatum.from_json(sales_datum)

        # discord message send
        discord_message = sales_bot.build_discord_message(data)
        webhook.send(embed=discord_message)

        # twitter message
        twitter_message = sales_bot.build_twitter_message(data)
        try:
            api.update_status(twitter_message)
        except tweepy.errors.Forbidden:
            continue


if __name__ == "__main__":
    bot_type = int(sys.argv[1])

    while True:
        main(bot_type)
        time.sleep(consts.SLEEP_TIME - 1)
