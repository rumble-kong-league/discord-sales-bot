from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING
import json
import os
import discord
import src.consts

# * https://stackoverflow.com/questions/744373/what-happens-when-using
# *-mutual-or-circular-cyclic-imports-in-python
if TYPE_CHECKING:
    from src.opensea import SalesDatum

# TODO: everything in this (collections) folder is not try
# TODO: consider creating a class and unifying these


def get_kong_boosts(kong_id: int) -> Dict[str, int]:

    meta_file = None
    this_path = os.path.dirname(os.path.realpath(__file__))
    meta_path = os.path.join(this_path, "meta", f"{kong_id}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_file = json.loads(f.read())["attributes"]

    boosts = {}

    for item in meta_file:
        if "display_type" not in item:
            continue

        trait_type = item["trait_type"]
        if trait_type in ["Vision", "Shooting", "Finish", "Defense"]:
            boosts[trait_type.lower()] = int(item["value"])

    boosts["cumulative"] = sum(boosts.values())

    return boosts


def build_kong_discord_message(data: List[SalesDatum]) -> discord.Embed:

    discord_messages = []

    def build_a_message(datum: SalesDatum) -> discord.Embed:

        is_bundle_sale = len(data) > 1
        description = (
            f"Price: {datum.price_eth()}"
            f" {datum.payment_symbol}, (${datum.price_usd():.2f})"
        )
        title = f"{datum.asset_name} Sold"
        url = f"{src.consts.KONG_ASSET_OPENSEA_URL}{datum.token_id}"

        if is_bundle_sale:
            title = f"Bundle: '{datum.bundle_name}' Sold"
            description = f"Bundle Total {description}"
            url = datum.bundle_link

        discord_message = discord.Embed(
            title=title,
            description=description,
            url=url,
        )

        discord_message.set_thumbnail(url=datum.image_url)
        if datum.boosts is not None:
            discord_message.add_field(
                name="Boost Total", value=datum.boosts["cumulative"], inline=False
            )
            discord_message.add_field(
                name="Defense", value=datum.boosts["defense"], inline=True
            )
            discord_message.add_field(
                name="Finish", value=datum.boosts["finish"], inline=True
            )
            discord_message.add_field(
                name="Shooting", value=datum.boosts["shooting"], inline=True
            )
            discord_message.add_field(
                name="Vision", value=datum.boosts["vision"], inline=True
            )

        discord_message.add_field(
            name="Seller",
            value=f"[{datum.seller}](https://opensea.io/{datum.seller_address})",
            inline=False,
        )
        discord_message.add_field(
            name="Buyer",
            value=f"[{datum.buyer}](https://opensea.io/{datum.buyer_address})",
            inline=True,
        )

        return discord_message

    # * we are repeating a bundle sale message n times because
    # * we are showing all the kongs / sneakers / rookies
    # * sold in that particular bundle. Notice that when it
    # * comes to building a twitter message. There is only
    # * one tweet per whole bundle.
    for datum in data:
        discord_messages.append(build_a_message(datum))

    return discord_messages


def build_kong_twitter_message(data: List[SalesDatum]) -> str:

    if not len(data) > 0:
        raise ValueError("No data to build a twitter message from")

    is_bundle_sale = len(data) > 1
    status_text = ""
    datum = data[0]

    if not is_bundle_sale:
        if datum.boosts is not None:
            status_text = (
                f"{datum.asset_name} bought for {datum.price_eth()} {datum.payment_symbol}, "
                + f"(${datum.price_usd():.2f})\n{datum.boosts['cumulative']} overall\n👀 "
                + f"{datum.boosts['vision']} | 🎯 {datum.boosts['shooting']}\n💪 "
                + f"{datum.boosts['finish']} | 🛡️ {datum.boosts['defense']} "
                + f"{src.consts.KONG_ASSET_OPENSEA_URL}{datum.token_id}"
            )
    else:
        status_text = (
            f"{datum.bundle_name} bought for {datum.price_eth()} {datum.payment_symbol}, "
            + f"(${datum.price_usd():.2f})\n"
            + f"{datum.bundle_link}"
        )

    return status_text
