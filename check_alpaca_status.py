import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()
KEY = os.getenv("KEY")
SECRET = os.getenv("SECRET")

if not KEY or not SECRET:
    raise ValueError("Missing KEY/SECRET in .env")

# IMPORTANT: match this to your Broker setting
paper = True

client = TradingClient(KEY, SECRET, paper=paper)

acct = client.get_account()
print("MODE:", "PAPER" if paper else "LIVE")
print("Account status:", acct.status)
print("Buying power:", acct.buying_power)
print("Cash:", acct.cash)

print("\nOPEN ORDERS:")
orders = client.get_orders()
if not orders:
    print("(none)")
else:
    for o in orders[:10]:
        print(o.symbol, o.side, o.qty, o.status)

print("\nPOSITIONS:")
positions = client.get_all_positions()
if not positions:
    print("(none)")
else:
    for p in positions:
        print(p.symbol, p.qty)
