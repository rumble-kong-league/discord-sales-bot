import logging
import requests


# ! implement email sending on error
def handle_exception() -> None:
    # ! gmail no longer supports app login with username and password
    # ! as such, can't use google to send emails
    logging.exception("")


def get_usd_price(symbol):
    url = "https://api.coinbase.com/v2/exchange-rates?currency=USD"
    resp = requests.get(url)
    if symbol == "WETH":
        symbol = "ETH"
    price = float(resp.json()["data"]["rates"][symbol])
    return 1 / price


def fetch_token_image_url(tokenId, contractAddress):
    url = f"https://api.opensea.io/api/v2/chain/ethereum/contract/{contractAddress}/nfts/{tokenId}"

    headers = {
        "accept": "application/json",
        "x-api-key": "9f5425ef0d3743d1988884e599d2ab6a",
    }

    resp = requests.get(url, headers=headers)

    resp_json = resp.json()
    return resp_json["nft"]["image_url"]
