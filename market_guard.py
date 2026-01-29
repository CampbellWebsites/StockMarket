import os
from alpaca.trading.client import TradingClient

key = os.getenv("KEY")
secret = os.getenv("SECRET")
paper = os.getenv("PAPER", "true").lower() == "true"

if not key or not secret:
    raise ValueError("Missing KEY/SECRET environment variables")

client = TradingClient(key, secret, paper=paper)
clock = client.get_clock()

if clock.is_open:
    print("Market is open ✅")
    raise SystemExit(0)

print("Market is closed ⛔ — skipping run")
raise SystemExit(1)
#testing