import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_SNEAKER_WEBHOOK = os.getenv("DISCORD_SNEAKER_WEBHOOK")
DISCORD_KONG_WEBHOOK = os.getenv("DISCORD_KONG_WEBHOOK")

TWEEPY_API_KEY = os.getenv("TWEEPY_API_KEY")
TWEEPY_API_SECRET = os.getenv("TWEEPY_API_SECRET")
TWEEPY_ACCESS_TOKEN = os.getenv("TWEEPY_ACCESS_TOKEN")
TWEEPY_ACCESS_TOKEN_SECRET = os.getenv("TWEEPY_ACCESS_TOKEN_SECRET")

OPENSEA_API_KEY = os.getenv("OPENSEA_API_KEY")

SLEEP_TIME = 30  # in seconds
OPENSEA_EVENTS_URL = "https://api.opensea.io/api/v1/events"

KONG_CONTRACT_ADDRESS = "0xef0182dc0574cd5874494a120750fd222fdb909a"
SNEAKER_CONTRACT_ADDRESS = "0x5180f2a553e76fac3cf019c8011711cf2b5c6035"

KONG_ASSET_OPENSEA_URL = f"https://opensea.io/assets/{KONG_CONTRACT_ADDRESS}/"
SNEAKER_ASSET_OPENSEA_URL = f"https://opensea.io/assets/{SNEAKER_CONTRACT_ADDRESS}/"

HEADERS = {
    "X-API-KEY": OPENSEA_API_KEY,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    + " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
}
