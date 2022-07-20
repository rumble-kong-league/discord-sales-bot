from typing import List
import discord

import src.consts

# * I think if we import SalesDatum we will get a circular dependency
# * SalesDatum is used for typing


def build_sneaker_discord_message(data: List["SalesDatum"]) -> List[discord.Embed]:

    discord_messages = []

    # TODO: not DRY, looks pretty much the same like the kongs bundler
    def build_a_message(datum: "SalesDatum") -> discord.Embed:

        is_bundle_sale = len(data) > 1
        # TODO: fix this hack
        msg_part_1 = f"Price: {datum.price_eth()}"
        msg_part_2 = f" {datum.payment_symbol}, (${datum.price_usd():.2f})"
        description = msg_part_1 + msg_part_2
        title = f"{datum.asset_name} Sold"
        url = f"{src.consts.SNEAKER_ASSET_OPENSEA_URL}{datum.token_id}"

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


def build_sneaker_twitter_message(data: List["SalesDatum"]) -> str:

    is_bundle_sale = len(data) > 1
    status_text = ""

    # TODO: not DRY
    if not is_bundle_sale:
        status_text = (
            f"{data[0].asset_name} bought for {data[0].price_eth()} {data[0].payment_symbol}, "
            + f"(${data[0].price_usd():.2f})\n"
            + f" {src.consts.SNEAKER_ASSET_OPENSEA_URL}{data[0].token_id}"
        )
    else:
        # TODO: fix this hack
        msg_part_1 = f"Bundle '{data[0].bundle_name}' bought"
        msg_part_2 = f" for {data[0].price_eth()} {data[0].payment_symbol}, "
        status_text = (
            msg_part_1
            + msg_part_2
            + f"(${data[0].price_usd():.2f})\n"
            + f" {data[0].bundle_link}"
        )

    return status_text
