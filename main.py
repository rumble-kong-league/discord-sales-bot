import os
from datetime import datetime, timedelta
from typing import Dict
from enum import Enum
import time
from discord import Webhook, RequestsWebhookAdapter
from dotenv import load_dotenv
import requests
import discord
import tweepy

load_dotenv()


SLEEP_TIME = 15  # in seconds


class TradeSide(Enum):
    Buyer = 0
    Seller = 1


# todo: should also support sneakers and any other RKL collections
RKL_CONTRACT_ADDRESS = "0xef0182dc0574cd5874494a120750fd222fdb909a"
RKL_ASSET_OPENSEA_URL = f"https://opensea.io/assets/{RKL_CONTRACT_ADDRESS}/"

DISCORD_KONG_WEBHOOK = os.getenv("DISCORD_KONG_WEBHOOK")
TWEEPY_API_KEY = os.getenv("TWEEPY_API_KEY")
TWEEPY_API_SECRET = os.getenv("TWEEPY_API_SECRET")
TWEEPY_ACCESS_TOKEN = os.getenv("TWEEPY_ACCESS_TOKEN")
TWEEPY_ACCESS_TOKEN_SECRET = os.getenv("TWEEPY_ACCESS_TOKEN_SECRET")
OPENSEA_API_KEY = os.getenv("OPENSEA_API_KEY")

headers = {
    "X-API-KEY": OPENSEA_API_KEY,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    + " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
}


def get_kong_boosts(kong_id: int) -> Dict[str, int]:
    """For a given kong id, returns its boosts.

    Args:
        kong_id (int): Kong's id

    Returns:
        Dict[str, int]: Kong's boosts
    """

    # todo: change to read this from file
    url = f"https://api.opensea.io/api/v1/asset/{RKL_CONTRACT_ADDRESS}/{kong_id}"
    response = requests.request("GET", url, headers=headers)
    traits = response.json()["traits"]
    boosts = {}

    for item in traits:
        item_trait_type = item["trait_type"]

        if item_trait_type == "Vision":
            boosts["vision"] = int(item["value"])

        elif item_trait_type == "Defense":
            boosts["defense"] = int(item["value"])

        elif item_trait_type == "Shooting":
            boosts["shooting"] = int(item["value"])

        elif item_trait_type == "Finish":
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


# todo: too-many-locals
# todo: too-many-statements
def main():
    """_summary_

    Raises:
        e: _description_
    """
    url = "https://api.opensea.io/api/v1/events"

    webhook = Webhook.from_url(DISCORD_KONG_WEBHOOK, adapter=RequestsWebhookAdapter())

    auth = tweepy.OAuthHandler(TWEEPY_API_KEY, TWEEPY_API_SECRET)
    auth.set_access_token(TWEEPY_ACCESS_TOKEN, TWEEPY_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    api.verify_credentials()

    ct = datetime.utcnow()
    dt = timedelta(minutes=3, seconds=30)
    pt = ct - dt
    pts = str(pt)
    # todo: what's this
    split_pts = pts.split(" ")
    ostime = f"{split_pts[0]}T{split_pts[1]}"

    querystring = {
        "asset_contract_address": RKL_CONTRACT_ADDRESS,
        "event_type": "successful",
        "only_opensea": "false",
        "occurred_after": ostime,
        "offset": 0,
        "limit": "50",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    sales_data = response.json()["asset_events"]

    for sales_datum in sales_data:

        name = sales_datum["asset"]["name"]
        image_url = sales_datum["asset"]["image_url"]
        token_id = sales_datum["asset"]["token_id"]
        total_price = sales_datum["total_price"]

        boosts = get_kong_boosts(token_id)

        buyer = get_trade_counter_party(TradeSide.Buyer, sales_datum)
        seller = get_trade_counter_party(TradeSide.Seller, sales_datum)
        buyer_address = sales_datum["winner_account"]["address"]
        seller_address = sales_datum["seller"]["address"]

        payment_symbol = sales_datum["payment_token"]["symbol"]
        payment_decimals = sales_datum["payment_token"]["decimals"]
        payment_usd = sales_datum["payment_token"]["usd_price"]

        price_eth = float(total_price) / 10 ** (payment_decimals)
        price_usd = price_eth * float(payment_usd)

        description = f"Price: {price_eth} {payment_symbol}, (${price_usd:.2f})"
        discord_message = discord.Embed(
            title=f"{name} Sold",
            description=description,
            url=f"{RKL_ASSET_OPENSEA_URL}{token_id}",
        )
        discord_message.set_thumbnail(url=image_url)
        discord_message.add_field(
            name="Boost Total", value=boosts["cumulative"], inline=False
        )
        discord_message.add_field(name="Defense", value=boosts["defense"], inline=True)
        discord_message.add_field(name="Finish", value=boosts["finish"], inline=True)
        discord_message.add_field(
            name="Shooting", value=boosts["shooting"], inline=True
        )
        discord_message.add_field(name="Vision", value=boosts["vision"], inline=True)
        discord_message.add_field(
            name="Seller",
            value=f"[{seller}](https://opensea.io/{seller_address})",
            inline=False,
        )
        discord_message.add_field(
            name="Buyer",
            value=f"[{buyer}](https://opensea.io/{buyer_address})",
            inline=True,
        )

        status_text = (
            f"{name} bought for {price_eth} {payment_symbol}, "
            + f"(${price_usd:.2f})\n{boosts['cumulative']} overall\n👀 {boosts['vision']}"
            + f" | 🎯 {boosts['shooting']}\n💪 {boosts['finish']} | 🛡️ {boosts['defense']}"
            + f" {RKL_ASSET_OPENSEA_URL}{token_id}"
        )

        webhook.send(embed=discord_message)
        api.update_status(status_text)  # Kong #3044 bought for 1.18Ξ ($5082.21)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(SLEEP_TIME)
