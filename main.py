import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict
from enum import Enum
import time
import json
from discord import Webhook, RequestsWebhookAdapter
from dotenv import load_dotenv
import requests
import discord
import tweepy

# todo: docs

load_dotenv()

DISCORD_KONG_WEBHOOK = os.getenv("DISCORD_KONG_WEBHOOK")
TWEEPY_API_KEY = os.getenv("TWEEPY_API_KEY")
TWEEPY_API_SECRET = os.getenv("TWEEPY_API_SECRET")
TWEEPY_ACCESS_TOKEN = os.getenv("TWEEPY_ACCESS_TOKEN")
TWEEPY_ACCESS_TOKEN_SECRET = os.getenv("TWEEPY_ACCESS_TOKEN_SECRET")
OPENSEA_API_KEY = os.getenv("OPENSEA_API_KEY")

SLEEP_TIME = 180  # in seconds
# todo: should also support sneakers and any other RKL collections
OPENSEA_EVENTS_URL = "https://api.opensea.io/api/v1/events"
RKL_CONTRACT_ADDRESS = "0xef0182dc0574cd5874494a120750fd222fdb909a"
RKL_ASSET_OPENSEA_URL = f"https://opensea.io/assets/{RKL_CONTRACT_ADDRESS}/"

HEADERS = {
    "X-API-KEY": OPENSEA_API_KEY,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    + " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
}


class TradeSide(Enum):
    Buyer = 0
    Seller = 1


@dataclass(frozen=True)
class SalesDatum:
    asset_name: str
    image_url: str
    token_id: int
    total_price: float

    buyer: str
    seller: str

    buyer_address: str
    seller_address: str

    payment_symbol: str
    payment_decimals: int
    payment_usd: float

    # todo: better type
    boosts: Dict

    @classmethod
    def from_json(cls, data: Dict):
        """_summary_

        Args:
            data (Dict): _description_

        Returns:
            _type_: _description_
        """

        asset_name = data["asset"]["name"]
        image_url = data["asset"]["image_url"]
        token_id = data["asset"]["token_id"]
        total_price = data["total_price"]

        # todo: read from files
        boosts = get_kong_boosts(token_id)

        buyer = get_trade_counter_party(TradeSide.Buyer, data)
        seller = get_trade_counter_party(TradeSide.Seller, data)

        buyer_address = data["winner_account"]["address"]
        seller_address = data["seller"]["address"]

        if buyer is None:
            buyer = buyer_address[:6]
        if seller is None:
            seller = seller_address[:6]

        payment_symbol = data["payment_token"]["symbol"]
        payment_decimals = data["payment_token"]["decimals"]
        payment_usd = data["payment_token"]["usd_price"]

        return cls(
            asset_name,
            image_url,
            token_id,
            total_price,
            buyer,
            seller,
            buyer_address,
            seller_address,
            payment_symbol,
            payment_decimals,
            payment_usd,
            boosts,
        )

    # todo: docs
    def price_eth(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return float(self.total_price) / (10**self.payment_decimals)

    def price_usd(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.price_eth() * float(self.payment_usd)


def get_kong_boosts(kong_id: int) -> Dict[str, int]:
    """For a given kong id, returns its boosts.

    Args:
        kong_id (int): Kong's id

    Returns:
        Dict[str, int]: Kong's boosts
    """

    meta_file = None

    with open(f"./meta/{kong_id}", "r", encoding="utf-8") as f:
        meta_file = json.loads(f.read())["attributes"]

    boosts = {}

    for item in meta_file:
        if "display_type" not in item:
            continue

        trait_type = item["trait_type"]

        if trait_type == "Vision":
            boosts["vision"] = int(item["value"])
        elif trait_type == "Defense":
            boosts["defense"] = int(item["value"])
        elif trait_type == "Shooting":
            boosts["shooting"] = int(item["value"])
        elif trait_type == "Finish":
            boosts["finish"] = int(item["value"])

    boosts["cumulative"] = sum(boosts.values())

    return boosts


def get_trade_counter_party(side: TradeSide, sales_datum: Dict) -> str:
    """
    Gets buyer or seller of the trade. If can't be found, returns 'Anon'.

    Args:
        side (TradeSide): Either buyer or seller.
        sales_datum (Dict): Opensea response dict.

    Raises:
        ValueError: If invalid trade side supplied.

    Returns:
        str: Trade counter party name.
    """

    trade_counter_party = ""

    if side == TradeSide.Buyer:
        try:
            trade_counter_party = sales_datum["winner_account"]["user"]["username"]
        except:
            trade_counter_party = sales_datum["winner_account"]["address"]
    elif side == TradeSide.Seller:
        try:
            trade_counter_party = sales_datum["seller"]["user"]["username"]
        except:
            trade_counter_party = sales_datum["seller"]["address"]
    else:
        raise ValueError("Invalid trade side")

    return trade_counter_party


def build_discord_message(data: SalesDatum) -> discord.Embed:
    """_summary_

    Args:
        data (SalesDatum): _description_

    Returns:
        discord.Embed: _description_
    """

    description = (
        f"Price: {data.price_eth()} {data.payment_symbol}, (${data.price_usd():.2f})"
    )
    discord_message = discord.Embed(
        title=f"{data.asset_name} Sold",
        description=description,
        url=f"{RKL_ASSET_OPENSEA_URL}{data.token_id}",
    )
    discord_message.set_thumbnail(url=data.image_url)
    discord_message.add_field(
        name="Boost Total", value=data.boosts["cumulative"], inline=False
    )
    discord_message.add_field(name="Defense", value=data.boosts["defense"], inline=True)
    discord_message.add_field(name="Finish", value=data.boosts["finish"], inline=True)
    discord_message.add_field(
        name="Shooting", value=data.boosts["shooting"], inline=True
    )
    discord_message.add_field(name="Vision", value=data.boosts["vision"], inline=True)
    discord_message.add_field(
        name="Seller",
        value=f"[{data.seller}](https://opensea.io/{data.seller_address})",
        inline=False,
    )
    discord_message.add_field(
        name="Buyer",
        value=f"[{data.buyer}](https://opensea.io/{data.buyer_address})",
        inline=True,
    )

    return discord_message


def build_twitter_message(data: SalesDatum) -> str:
    """_summary_

    Args:
        data (SalesDatum): _description_

    Returns:
        str: _description_
    """

    status_text = (
        f"{data.asset_name} bought for {data.price_eth()} {data.payment_symbol}, "
        + f"(${data.price_usd():.2f})\n{data.boosts['cumulative']} overall\n👀 "
        + f"{data.boosts['vision']} | 🎯 {data.boosts['shooting']}\n💪 "
        + f"{data.boosts['finish']} | 🛡️ {data.boosts['defense']} "
        + f"{RKL_ASSET_OPENSEA_URL}{data.token_id}"
    )

    return status_text


def main():
    """
    If any sales happen, this will push a message to a Discord channel with details.
    This will also use tweepy to post a message on Twitter.
    """

    # todo: all of this should be done once, ideally in a class
    webhook = Webhook.from_url(DISCORD_KONG_WEBHOOK, adapter=RequestsWebhookAdapter())
    auth = tweepy.OAuthHandler(TWEEPY_API_KEY, TWEEPY_API_SECRET)
    auth.set_access_token(TWEEPY_ACCESS_TOKEN, TWEEPY_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    api.verify_credentials()

    current_time = datetime.utcnow()
    previous_time = current_time - timedelta(seconds=SLEEP_TIME - 1)
    opensea_time = str(previous_time).replace(" ", "T")

    querystring = {
        "asset_contract_address": RKL_CONTRACT_ADDRESS,
        "event_type": "successful",
        "only_opensea": "false",
        "occurred_after": opensea_time,
        "offset": 0,
        "limit": "50",
    }

    response = requests.request(
        "GET", OPENSEA_EVENTS_URL, headers=HEADERS, params=querystring
    )
    response_json = response.json()
    sales_data = response_json["asset_events"]

    for sales_datum in sales_data:

        # build sales data from json
        data = SalesDatum.from_json(sales_datum)

        # discord message send
        discord_message = build_discord_message(data)
        webhook.send(embed=discord_message)

        # twitter message
        twitter_message = build_twitter_message(data)
        try:
            api.update_status(twitter_message)
        except tweepy.errors.Forbidden:
            continue


if __name__ == "__main__":
    while True:
        main()
        time.sleep(SLEEP_TIME - 1)
