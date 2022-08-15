from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

# import numpy as np
# import PIL
# from PIL import Image
# import requests

from src.kongs import get_kong_boosts


class TradeSide(Enum):
    Buyer = 0
    Seller = 1


@dataclass(frozen=True)
class SalesDatum:
    bundle_name: Optional[str]
    bundle_link: Optional[str]

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

    # * we require these two to know which
    # * trades to publish to discord and twitter
    transaction_index: int
    transaction_block: int

    # todo: better type (dataclass to hold boosts)
    boosts: Optional[Dict]

    # TODO: this is pretty poo. Refactor.
    @classmethod
    def from_json(cls, data: Dict) -> List["SalesDatum"]:

        is_bundle = data["asset_bundle"] is not None

        if not is_bundle:
            asset_name = data["asset"]["name"]
            image_url = data["asset"]["image_url"]
            token_id = data["asset"]["token_id"]
            total_price = data["total_price"]

            # rationale for this is that kongs can have any name
            # so it is easier to check that event is not about
            # sneakers
            boosts = None
            if asset_name is not None:
                is_sneaks = asset_name.startswith("RKL Sneakers")
                is_rooks = asset_name.startswith("Rookie")
                if not is_sneaks and not is_rooks:
                    boosts = get_kong_boosts(token_id)

            buyer = get_trade_counter_party(TradeSide.Buyer, data)
            seller = get_trade_counter_party(TradeSide.Seller, data)

            buyer_address = data["winner_account"]["address"]
            seller_address = data["seller"]["address"]

            if buyer == "":
                buyer = buyer_address[:6]
            if seller == "":
                seller = seller_address[:6]

            payment_symbol = data["payment_token"]["symbol"]
            payment_decimals = data["payment_token"]["decimals"]
            payment_usd = data["payment_token"]["usd_price"]

            transaction_index = int(data["transaction"]["transaction_index"])
            transaction_block = int(data["transaction"]["block_number"])

            return [
                cls(
                    None,
                    None,
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
                    transaction_index,
                    transaction_block,
                    boosts,
                )
            ]
        else:
            # TODO: not DRY
            bundle_name = data["asset_bundle"]["name"]
            bundle_link = data["asset_bundle"]["permalink"]

            asset_names = [asset["name"] for asset in data["asset_bundle"]["assets"]]
            image_urls = [
                asset["image_url"] for asset in data["asset_bundle"]["assets"]
            ]
            token_ids = [asset["token_id"] for asset in data["asset_bundle"]["assets"]]
            total_price = data["total_price"]
            # * this is how you would stack them horizontally
            # imgs = [Image.open(requests.get(i, stream=True).raw) for i in urls]
            # min_shape = sorted([(np.sum(i.size), i.size ) for i in imgs])[0][1]
            # imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in imgs))
            # imgs_comb = Image.fromarray(imgs_comb)

            # rationale for this is that kongs can have any name
            # so it is easier to check that event is not about
            # sneakers
            first_asset_name = data["asset_bundle"]["assets"][0]["name"]
            boosts = []
            is_sneakers = first_asset_name.startswith("RKL Sneakers")
            if not is_sneakers:
                for asset in data["asset_bundle"]["assets"]:
                    boosts.append(get_kong_boosts(asset["token_id"]))

            buyer = get_trade_counter_party(TradeSide.Buyer, data)
            seller = get_trade_counter_party(TradeSide.Seller, data)

            buyer_address = data["winner_account"]["address"]
            seller_address = data["seller"]["address"]

            if buyer == "":
                buyer = buyer_address[:6]
            if seller == "":
                seller = seller_address[:6]

            payment_symbol = data["payment_token"]["symbol"]
            payment_decimals = data["payment_token"]["decimals"]
            payment_usd = data["payment_token"]["usd_price"]

            transaction_index = int(data["transaction"]["transaction_index"])
            transaction_block = int(data["transaction"]["block_number"])

            items = []

            for i in range(len(asset_names)):
                items.append(
                    cls(
                        bundle_name,
                        bundle_link,
                        asset_names[i],
                        image_urls[i],
                        token_ids[i],
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
                        None if is_sneakers else boosts[i],
                    )
                )

            return items

    def price_eth(self) -> float:
        return float(self.total_price) / (10**self.payment_decimals)

    def price_usd(self) -> float:
        return self.price_eth() * float(self.payment_usd)


def get_trade_counter_party(side: TradeSide, sales_datum: Dict) -> str:

    trade_counter_party = ""

    if side == TradeSide.Buyer:
        try:
            trade_counter_party = sales_datum["winner_account"]["user"]["username"]
        except:
            trade_counter_party = str(sales_datum["winner_account"]["address"])
    elif side == TradeSide.Seller:
        try:
            trade_counter_party = sales_datum["seller"]["user"]["username"]
        except:
            trade_counter_party = str(sales_datum["seller"]["address"])
    else:
        raise ValueError("Invalid trade side")

    return trade_counter_party
