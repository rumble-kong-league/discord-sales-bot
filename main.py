import os
from datetime import datetime, timedelta
from typing import Dict
from discord import Webhook, RequestsWebhookAdapter
from dotenv import load_dotenv
import requests
import discord
import tweepy

load_dotenv()

# todo: better names to understand what these keys are for

RKL_CONTRACT = "0xef0182dc0574cd5874494a120750fd222fdb909a"

CHANNEL_URL = os.getenv("CHANNEL_URL")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
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
    url = (
        "https://api.opensea.io/api/v1/asset/0xef0182dc0574cd5874494a120750fd222fdb909a/"
        + str(kong_id)
    )
    response = requests.request("GET", url, headers=headers)
    traits = response.json()["traits"]
    boosts = {}

    for item in traits:
        item_trait_type = item["trait_type"]
        value = int(item["value"])

        if item_trait_type == "Vision":
            boosts["vision"] = value

        elif item_trait_type == "Defense":
            boosts["defense"] = value

        elif item_trait_type == "Shooting":
            boosts["shooting"] = value

        elif item_trait_type == "Finish":
            boosts["finish"] = value

    boosts["cumulative"] = sum(boosts.values())

    return boosts


# todo: too-many-locals
# todo: too-many-statements
def cronjob():
    """_summary_

    Raises:
        e: _description_
    """
    url = "https://api.opensea.io/api/v1/events"

    webhook = Webhook.from_url(CHANNEL_URL, adapter=RequestsWebhookAdapter())

    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    api.verify_credentials()

    print(f"Checking contract {RKL_CONTRACT} for new sales")

    # get current time in utc time zone
    ct = datetime.utcnow()
    # specify time range
    dt = timedelta(minutes=3, seconds=30)
    pt = ct - dt
    # create string for opensea
    pts = str(pt)
    ostime = pts.split(" ", maxsplit=1)[0] + "T" + pts.split(" ")[1]

    querystring = {
        "asset_contract_address": RKL_CONTRACT,
        "event_type": "successful",
        "only_opensea": "false",
        "occurred_after": ostime,
        "offset": 0,
        "limit": "50",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    # getting sales data
    sales_data = response.json()["asset_events"]
    print(sales_data)

    for sales_datum in sales_data:

        name = sales_datum["asset"]["name"]
        image_url = sales_datum["asset"]["image_url"]
        token_id = sales_datum["asset"]["token_id"]

        boosts = get_kong_boosts(token_id)

        try:
            buyer = sales_datum["winner_account"]["user"]["username"]
        except:
            buyer = "Anon"

        buyer_address = sales_datum["winner_account"]["address"]
        total_price = sales_datum["total_price"]

        try:
            seller = sales_datum["seller"]["user"]["username"]
        except:
            seller = "Anon"

        seller_address = sales_datum["seller"]["address"]
        payment_symbol = sales_datum["payment_token"]["symbol"]
        payment_decimals = sales_datum["payment_token"]["decimals"]
        payment_USD = sales_datum["payment_token"]["usd_price"]
        timestamp = sales_datum["transaction"]["timestamp"]
        tx_hash = sales_datum["transaction"]["transaction_hash"]

        price_eth = float(total_price) / 10 ** (payment_decimals)
        price_usd = price_eth * float(payment_USD)

        if buyer is None:
            buyer = buyer_address[0:6]
        if seller is None:
            seller = seller_address[0:6]

        print("Buyer: ", buyer, " ", buyer_address)
        print("Seller: ", seller, " ", seller_address)
        print(f"Price: {price_eth} {payment_symbol}")
        print("Price: $", price_usd)
        print("Timestamp: ", timestamp)
        print("Tx Hash: ", tx_hash)
        print(boosts)

        desc = f"Price: {price_eth} {payment_symbol}, (${price_usd:.2f})"
        embedVar = discord.Embed(
            title=name + " Sold",
            description=desc,
            url="https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/"
            + token_id,
        )
        embedVar.set_thumbnail(url=image_url)
        embedVar.add_field(name="Boost Total", value=boosts["cumulative"], inline=False)
        embedVar.add_field(name="Defense", value=boosts["defense"], inline=True)
        embedVar.add_field(name="Finish", value=boosts["finish"], inline=True)
        embedVar.add_field(name="Shooting", value=boosts["shooting"], inline=True)
        embedVar.add_field(name="Vision", value=boosts["vision"], inline=True)
        embedVar.add_field(
            name="Seller",
            value="[" + seller + "]" + "(https://opensea.io/" + seller_address + ")",
            inline=False,
        )
        embedVar.add_field(
            name="Buyer",
            value="[" + buyer + "]" + "(https://opensea.io/" + buyer_address + ")",
            inline=True,
        )

        status_text = (
            f"{name} bought for {price_eth} {payment_symbol}, "
            + f"(${price_usd:.2f})\n{boosts['cumulative']} overall\n👀 {boosts['vision']}"
            + f" | 🎯 {boosts['shooting']}\n💪 {boosts['finish']} | 🛡️ {boosts['defense']}"
            + f" https://opensea.io/assets/0xef0182dc0574cd5874494a120750fd222fdb909a/{token_id}"
        )

        webhook.send(embed=embedVar)
        api.update_status(status_text)  # Kong #3044 bought for 1.18Ξ ($5082.21)

        # Send Tweet
