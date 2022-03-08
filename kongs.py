import json
from typing import Dict
import discord

import consts


def get_kong_boosts(kong_id: int) -> Dict[str, int]:
    """For a given kong id, returns its boosts.

    Args:
        kong_id (int): Kong's id.

    Returns:
        Dict[str, int]: Kong's boosts.
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


def build_kong_discord_message(data: "SalesDatum") -> discord.Embed:
    """
    Builds a sale message for Discord.

    Args:
        data (SalesDatum): All the data required for the message.

    Returns:
        discord.Embed: discord embed message.
    """

    description = (
        f"Price: {data.price_eth()} {data.payment_symbol}, (${data.price_usd():.2f})"
    )
    discord_message = discord.Embed(
        title=f"{data.asset_name} Sold",
        description=description,
        url=f"{consts.KONG_ASSET_OPENSEA_URL}{data.token_id}",
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


def build_kong_twitter_message(data: "SalesDatum") -> str:
    """
    Builds a sale message for Twitter.

    Args:
        data (SalesDatum): All the data required for the message.

    Returns:
        str: twitter message.
    """

    status_text = (
        f"{data.asset_name} bought for {data.price_eth()} {data.payment_symbol}, "
        + f"(${data.price_usd():.2f})\n{data.boosts['cumulative']} overall\n👀 "
        + f"{data.boosts['vision']} | 🎯 {data.boosts['shooting']}\n💪 "
        + f"{data.boosts['finish']} | 🛡️ {data.boosts['defense']} "
        + f"{consts.KONG_ASSET_OPENSEA_URL}{data.token_id}"
    )

    return status_text
