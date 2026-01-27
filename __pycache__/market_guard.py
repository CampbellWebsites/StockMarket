import os
from alpaca.trading.client import TradingClient

key = os.getenv("PKHM5U4ZQZM47RKRUD7OZJPIH7")
secret = os.getenv("H5w1sSUDS3SJZx4vcEFUYAPCSdacXDyYF18yns956HC")
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
