from typing import Dict, List
import json
import os
import discord

import src.consts


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


def build_kong_discord_message(data: List["SalesDatum"]) -> discord.Embed:

    discord_messages = []

    def build_a_message(datum: "SalesDatum") -> discord.Embed:

        is_bundle_sale = len(data) > 1
        # TODO: fix this hack
        msg_part_1 = f"Price: {datum.price_eth()} "
        msg_part_2 = f"{datum.payment_symbol}, (${datum.price_usd():.2f})"
        description = msg_part_1 + msg_part_2
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

    for datum in data:
        discord_messages.append(build_a_message(datum))

    return discord_messages


def build_kong_twitter_message(data: List["SalesDatum"]) -> str:

    is_bundle_sale = len(data) > 1
    status_text = ""

    # TODO: not DRY
    if not is_bundle_sale:
        status_text = (
            f"{data[0].asset_name} bought for {data[0].price_eth()} {data[0].payment_symbol}, "
            + f"(${data[0].price_usd():.2f})\n{data[0].boosts['cumulative']} overall\n👀 "
            + f"{data[0].boosts['vision']} | 🎯 {data[0].boosts['shooting']}\n💪 "
            + f"{data[0].boosts['finish']} | 🛡️ {data[0].boosts['defense']} "
            + f"{src.consts.KONG_ASSET_OPENSEA_URL}{data[0].token_id}"
        )
    else:
        status_text = (
            f"{data[0].bundle_name} bought for {data[0].price_eth()} {data[0].payment_symbol}, "
            + f"(${data[0].price_usd():.2f})\n"
            + f"{data[0].bundle_link}"
        )

    return status_text
