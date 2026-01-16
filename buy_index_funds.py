import os
from dotenv import load_dotenv
from broker import Broker

load_dotenv()

KEY = os.getenv("KEY")
SECRET = os.getenv("SECRET")

if not KEY or not SECRET:
    raise ValueError("Missing KEY/SECRET in .env")

# PAPER TRADING FIRST
broker = Broker(KEY, SECRET, paper=True)

# Buy some index ETFs
broker.buy("VOO", 1)   # S&P 500
broker.buy("QQQ", 1)   # Nasdaq-100 (optional)
