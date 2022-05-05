from typing import Dict
from typing import List
from enum import Enum
from dataclasses import dataclass

from kong_helpers import get_kong_boosts


class TradeSide(Enum):
    Buyer = 0
    Seller = 1


@dataclass(frozen=True)
class Asset:
    asset_name: str
    image_url: str
    token_id: int
    permalink: str

    # todo: better type (dataclass to hold boosts)
    boosts: Dict

    @classmethod
    def from_json(cls, data: Dict) -> "Asset":
        """
        Instanties Asset from OpenSea's response.

        Args:
            data (Dict): Opensea's event["asset"] response.

        Returns:
            Asset: instance.
        """

        asset_name = data["name"]
        if asset_name is None:
            asset_name = "None"
        image_url = data["image_url"]
        token_id = data["token_id"]
        permalink = data["permalink"]

        # rationale for this is that kongs can have any name
        # so it is easier to check that event is not about
        # sneakers
        boosts = None
        if asset_name != "None" and not asset_name.startswith("RKL Sneakers"):
            boosts = get_kong_boosts(token_id)

        return cls(asset_name, image_url, token_id, permalink, boosts)


@dataclass(frozen=True)
class AssetBundle:
    name: str
    permalink: str
    assets: List[Asset]

    @classmethod
    def from_json(cls, data: Dict) -> "AssetBundle":
        """
        Instanties AssetBundle from OpenSea's response.

        Args:
            data (Dict): Opensea's event["asset_bundle"] response.

        Returns:
            Asset: instance.
        """

        name = data["name"]
        permalink = data["permalink"]

        assets = []
        for asset in data["assets"]:
            assets.append(Asset.from_json(asset))

        return cls(name, permalink, assets)


@dataclass(frozen=True)
class SalesDatum:
    asset: Asset
    asset_bundle: AssetBundle
    total_price: float

    buyer: str
    seller: str

    buyer_address: str
    seller_address: str

    payment_symbol: str
    payment_decimals: int
    payment_usd: float

    # * we require these two to know which
    # * trades to publish to discord and twitter
    transaction_index: int
    transaction_block: int

    @classmethod
    def from_json(cls, data: Dict) -> "SalesDatum":
        """
        Instanties SalesDatum from OpenSea's response.

        Args:
            data (Dict): Opensea's event response.

        Returns:
            SalesDatum: instance.
        """

        asset_bundle = None
        asset = None
        if "asset_bundle" in data and data["asset_bundle"] is not None:
            asset_bundle = AssetBundle.from_json(data["asset_bundle"])
            asset = None
        else:
            asset = Asset.from_json(data["asset"])
            asset_bundle = None

        total_price = data["total_price"]

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

        transaction_index = int(data["transaction"]["transaction_index"])
        transaction_block = int(data["transaction"]["block_number"])

        return cls(
            asset,
            asset_bundle,
            total_price,
            buyer,
            seller,
            buyer_address,
            seller_address,
            payment_symbol,
            payment_decimals,
            payment_usd,
            transaction_index,
            transaction_block,
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

    def display_name(self) -> str:
        """
        Get the display name from the Asset or Bundle.

        Returns:
            str: The display name
        """
        if self.asset_bundle is None:
            return self.asset.asset_name

        return f"Bundle: {self.asset_bundle.name}"

    def permalink(self) -> str:
        """
        Get the permalink from the Asset or Bundle.

        Returns:
            str: The permalink
        """
        if self.asset_bundle is None:
            return self.asset.permalink

        return self.asset_bundle.permalink

    def image_url(self) -> str:
        """
        Get the image URL from the Asset or Bundle.

        Returns:
            str: The image URL
        """
        if self.asset_bundle is None:
            return self.asset.image_url

        return self.asset_bundle.assets[0].image_url


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
