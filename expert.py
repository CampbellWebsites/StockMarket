import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# Load environment variables
load_dotenv()

API_KEY = os.getenv("KEY")
API_SECRET = os.getenv("SECRET")

BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(
    key_id=API_KEY,
    secret_key=API_SECRET,
    base_url=BASE_URL,
    api_version="v2"
)

SYMBOL = "AAPL"
QTY = 1

try:
    # Check if the asset is shortable
    asset = api.get_asset(SYMBOL)
    if not asset.shortable:
        raise Exception(f"{SYMBOL} is not shortable")

    # Get latest quote
    quote = api.get_latest_quote(SYMBOL)
    bid_price = float(quote.bid_price)

    # Slightly below bid to improve fill
    limit_price = round(bid_price * 0.99, 2)

    order = api.submit_order(
        symbol=SYMBOL,
        qty=QTY,
        side="sell",          # sell-to-open (short)
        type="limit",
        limit_price=limit_price,
        time_in_force="day",
        extended_hours=True
    )

    print("Short sell order submitted:")
    print(order)

except Exception as e:
    print("Order failed:")
    print(e)
