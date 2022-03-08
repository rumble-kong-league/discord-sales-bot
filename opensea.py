from typing import Dict
from enum import Enum
from dataclasses import dataclass

from kongs import get_kong_boosts


class TradeSide(Enum):
    Buyer = 0
    Seller = 1


@dataclass(frozen=True)
class SalesDatum:
    asset_name: str
    image_url: str
    token_id: int
    total_price: float

    buyer: str
    seller: str

    buyer_address: str
    seller_address: str

    payment_symbol: str
    payment_decimals: int
    payment_usd: float

    # todo: better type (dataclass to hold boosts)
    boosts: Dict

    @classmethod
    def from_json(cls, data: Dict) -> "SalesDatum":
        """
        Instanties SalesDatum from OpenSea's response.

        Args:
            data (Dict): Opensea's event response.

        Returns:
            SalesDatum: instance.
        """

        asset_name = data["asset"]["name"]
        image_url = data["asset"]["image_url"]
        token_id = data["asset"]["token_id"]
        total_price = data["total_price"]

        # rationale for this is that kongs can have any name
        # so it is easier to check that event is not about
        # sneakers
        if not asset_name.startswith("RKL Sneakers"):
            boosts = get_kong_boosts(token_id)

        buyer = get_trade_counter_party(TradeSide.Buyer, data)
        seller = get_trade_counter_party(TradeSide.Seller, data)

        buyer_address = data["winner_account"]["address"]
        seller_address = data["seller"]["address"]

        if buyer is None:
            buyer = buyer_address[:6]
        if seller is None:
            seller = seller_address[:6]

        payment_symbol = data["payment_token"]["symbol"]
        payment_decimals = data["payment_token"]["decimals"]
        payment_usd = data["payment_token"]["usd_price"]

        return cls(
            asset_name,
            image_url,
            token_id,
            total_price,
            buyer,
            seller,
            buyer_address,
            seller_address,
            payment_symbol,
            payment_decimals,
            payment_usd,
            boosts,
        )

    def price_eth(self) -> float:
        """
        Converts the sale price into eth price. For example, the original
        sale might have been in USDC.

        Returns:
            float: ether equivalent price of the sale.
        """
        return float(self.total_price) / (10**self.payment_decimals)

    def price_usd(self) -> float:
        """
        Converts the sale price into usd price.

        Returns:
            float: usd equivalent price of the sale.
        """
        return self.price_eth() * float(self.payment_usd)


def get_trade_counter_party(side: TradeSide, sales_datum: Dict) -> str:
    """
    Gets buyer or seller of the trade. If can't be found, returns address.

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
