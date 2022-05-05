import discord
from opensea import SalesDatum


def build_kong_discord_message(data: SalesDatum) -> discord.Embed:
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
        title=f"{data.display_name()} Sold",
        description=description,
        url=f"{data.permalink()}",
    )
    discord_message.set_thumbnail(url=data.image_url())

    if data.asset_bundle is None and data.asset.boosts is not None:
        discord_message.add_field(
            name="Boost Total", value=data.asset.boosts["cumulative"], inline=False
        )
        discord_message.add_field(
            name="Defense", value=data.asset.boosts["defense"], inline=True
        )
        discord_message.add_field(
            name="Finish", value=data.asset.boosts["finish"], inline=True
        )
        discord_message.add_field(
            name="Shooting", value=data.asset.boosts["shooting"], inline=True
        )
        discord_message.add_field(
            name="Vision", value=data.asset.boosts["vision"], inline=True
        )

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


def build_kong_twitter_message(data: SalesDatum) -> str:
    """
    Builds a sale message for Twitter.

    Args:
        data (SalesDatum): All the data required for the message.

    Returns:
        str: twitter message.
    """

    boost_text = ""
    if data.asset_bundle is None and data.asset.boosts is not None:
        boost_text = (
            f"{data.asset.boosts['cumulative']} overall\n👀 "
            + f"{data.asset.boosts['vision']} | 🎯 {data.asset.boosts['shooting']}\n💪 "
            + f"{data.asset.boosts['finish']} | 🛡️ {data.asset.boosts['defense']} "
        )

    status_text = (
        f"{data.display_name()} bought for {data.price_eth()} {data.payment_symbol}, "
        + f"(${data.price_usd():.2f})\n"
        + boost_text
        + data.permalink()
    )

    return status_text
