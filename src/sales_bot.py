from typing import Union, List
from enum import Enum, unique

import discord

from src.collections.kongs import build_kong_discord_message, build_kong_twitter_message
from src.collections.sneakers import (
    build_sneaker_discord_message,
    build_sneaker_twitter_message,
)
from src.collections.rookies import (
    build_rookie_discord_message,
    build_rookie_twitter_message,
)
from src.opensea import SalesDatum

import src.consts


@unique
class SalesBotType(Enum):
    KONG = 0
    SNEAKER = 1
    ROOKIE = 2

    @classmethod
    def from_int(cls, v: int) -> "SalesBotType":
        if v == 0:
            return cls.KONG
        elif v == 1:
            return cls.SNEAKER
        elif v == 2:
            return cls.ROOKIE
        else:
            raise ValueError(f"Cannot instantiate from {v}")


class SalesBot:
    def __init__(self, sales_bot_type: Union[SalesBotType, int]):

        if isinstance(sales_bot_type, int):
            self.sales_bot_type = SalesBotType.from_int(sales_bot_type)
        # ! note that this else contains all NON int types
        # ! ideally this branch only deals with SalesBotType
        else:
            self.sales_bot_type = sales_bot_type

        if self.sales_bot_type == SalesBotType.KONG:
            self.discord_webhook = src.consts.DISCORD_KONG_WEBHOOK
            self.asset_contract_address = src.consts.KONG_CONTRACT_ADDRESS
        elif self.sales_bot_type == SalesBotType.SNEAKER:
            self.discord_webhook = src.consts.DISCORD_SNEAKER_WEBHOOK
            self.asset_contract_address = src.consts.SNEAKER_CONTRACT_ADDRESS
        elif self.sales_bot_type == SalesBotType.ROOKIE:
            self.discord_webhook = src.consts.DISCORD_ROOKIE_WEBHOOK
            self.asset_contract_address = src.consts.ROOKIE_CONTRACT_ADDRESS
        else:
            raise ValueError("Invalid sales_bot_type.")

    def build_discord_messages(self, data: List[SalesDatum]) -> List[discord.Embed]:
        if self.sales_bot_type == SalesBotType.KONG:
            return build_kong_discord_message(data)
        elif self.sales_bot_type == SalesBotType.SNEAKER:
            return build_sneaker_discord_message(data)
        elif self.sales_bot_type == SalesBotType.ROOKIE:
            return build_rookie_discord_message(data)
        else:
            raise ValueError("Invalid sales_bot_type")

    def build_twitter_message(self, data: List[SalesDatum]) -> str:
        if self.sales_bot_type == SalesBotType.KONG:
            return build_kong_twitter_message(data)
        elif self.sales_bot_type == SalesBotType.SNEAKER:
            return build_sneaker_twitter_message(data)
        elif self.sales_bot_type == SalesBotType.ROOKIE:
            return build_rookie_twitter_message(data)
        else:
            raise ValueError("Invalid sales_bot_type")


def is_fresh_sale(datum: SalesDatum, since_block: int, since_index: int) -> bool:
    if datum.transaction_block > since_block:
        return True

    if datum.transaction_block == since_block:
        if datum.transaction_index > since_index:
            return True

    return False
