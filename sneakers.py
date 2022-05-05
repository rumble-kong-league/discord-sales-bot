import discord
from opensea import SalesDatum


def build_sneaker_discord_message(data: SalesDatum) -> discord.Embed:
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
        url=data.permalink(),
    )
    discord_message.set_thumbnail(url=data.image_url())
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


def build_sneaker_twitter_message(data: SalesDatum) -> str:
    """
    Builds a sale message for Twitter.

    Args:
        data (SalesDatum): All the data required for the message.

    Returns:
        str: twitter message.
    """

    status_text = (
        f"{data.display_name()} bought for {data.price_eth()} {data.payment_symbol}, "
        + f"(${data.price_usd():.2f})\n"
        + f" {data.permalink()}"
    )

    return status_text
