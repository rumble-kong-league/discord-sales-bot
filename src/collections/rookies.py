from __future__ import annotations
from typing import List, TYPE_CHECKING
import discord
import src.consts

# * https://stackoverflow.com/questions/744373/what-happens-when-using
# *-mutual-or-circular-cyclic-imports-in-python
if TYPE_CHECKING:
    from src.opensea import SalesDatum


def build_rookie_discord_message(data: List[SalesDatum]) -> discord.Embed:
    discord_messages = []

    def build_a_message(datum: SalesDatum) -> discord.Embed:
        is_bundle_sale = len(data) > 1
        description = (
            f"Price: {datum.price_eth()}"
            f" {datum.payment_symbol}, (${datum.price_usd():.2f})"
        )
        title = f"{datum.asset_name} Sold"
        url = f"{src.consts.ROOKIE_ASSET_OPENSEA_URL}{datum.token_id}"

        if is_bundle_sale:
            title = f"Bundle: '{datum.bundle_name}' Sold"
            description = f"Bundle Total {description}"
            url = datum.bundle_link

        discord_message = discord.Embed(
            title=title,
            description=description,
            url=url,
        )

        # ! can safely remove this after all rookies reveal
        if datum.image_url is not None:
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

    # * we are repeating a bundle sale message n times because
    # * we are showing all the kongs / sneakers / rookies
    # * sold in that particular bundle. Notice that when it
    # * comes to building a twitter message. There is only
    # * one tweet per whole bundle.
    for datum in data:
        discord_messages.append(build_a_message(datum))

    return discord_messages


def build_rookie_twitter_message(data: List[SalesDatum]) -> str:
    if not len(data) > 0:
        raise ValueError("No data to build a twitter message from")

    is_bundle_sale = len(data) > 1
    status_text = ""
    datum = data[0]

    if not is_bundle_sale:
        status_text = (
            f"{datum.asset_name} bought for {datum.price_eth()} {datum.payment_symbol}, "
            + f"(${datum.price_usd():.2f})\n"
            + f"{src.consts.ROOKIE_ASSET_OPENSEA_URL}{datum.token_id}"
        )
    else:
        status_text = (
            f"{datum.bundle_name} bought for {datum.price_eth()} {datum.payment_symbol}, "
            + f"(${datum.price_usd():.2f})\n"
            + f"{datum.bundle_link}"
        )

    return status_text
