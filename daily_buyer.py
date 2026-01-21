print("daily_buyer.py started")


import os
from broker import Broker
import broker
print("BROKER FILE:", broker.__file__)
print("Broker has buy_dollars:", hasattr(Broker, "buy_dollars"))
from dotenv import load_dotenv
import yfinance as yf

from broker import Broker
import time
from pathlib import Path

LOCK = Path(".last_run_epoch")

def ran_within_last_hour() -> bool:
    if not LOCK.exists():
        return False
    try:
        last = float(LOCK.read_text().strip())
        return (time.time() - last) < 3600
    except Exception:
        return False

def mark_ran_now():
    LOCK.write_text(str(time.time()))


load_dotenv()
KEY = os.getenv("KEY")
SECRET = os.getenv("SECRET")

if not KEY or not SECRET:
    raise ValueError("Missing KEY/SECRET in .env")

PAPER = True               # KEEP TRUE for now
DAILY_DOLLARS = 500
ETF_LIST = ["VOO", "SPY"]
UNIVERSE_FILE = "universe.txt"


def load_universe() -> list[str]:
    with open(UNIVERSE_FILE, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    # don’t let ETFs be chosen as "top 2 stocks"
    tickers = [t for t in tickers if t not in ETF_LIST]
    return tickers


def one_day_percent_change(symbol: str) -> float | None:
    hist = yf.Ticker(symbol).history(period="5d")
    closes = hist["Close"].dropna().tolist()
    if len(closes) < 2:
        return None
    prev_close = closes[-2]
    last_close = closes[-1]
    if prev_close <= 0:
        return None
    return (last_close - prev_close) / prev_close


def pick_top2(tickers: list[str]) -> list[str]:
    scored = []
    no_data = 0

    for t in tickers:
        try:
            pct = one_day_percent_change(t)
            if pct is None:
                no_data += 1
                continue
            scored.append((pct, t))
        except Exception:
            no_data += 1
            continue

    print("Tickers with data:", len(scored), "| skipped:", no_data)

    scored.sort(reverse=True, key=lambda x: x[0])
    top2 = [t for _, t in scored[:2]]

    # fallback (so it ALWAYS buys 2 stocks)
    if len(top2) < 2:
        fallback = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
        for f in fallback:
            if f not in top2 and f in tickers:
                top2.append(f)
            if len(top2) == 2:
                break

    return top2



def main():
    if ran_within_last_hour():
        print("Already ran in the last hour — skipping.")
    return

    broker = Broker(KEY, SECRET, paper=PAPER)

    acct = broker.client.get_account()
    buying_power = float(acct.buying_power)

    planned_spend = DAILY_DOLLARS * (len(ETF_LIST) + 2)
    print("MODE:", "PAPER" if PAPER else "LIVE")
    print("Buying power:", buying_power)
    print("Planned spend:", planned_spend)

    if planned_spend > buying_power:
        print("Not enough buying power. Stop.")
        return

    # 1) Buy ETFs
    for etf in ETF_LIST:
        broker.buy_dollars(etf, DAILY_DOLLARS)

    # 2) Pick top 2 performers from your universe
    universe = load_universe()
    print("Universe size:", len(universe))
    print("First 10 tickers:", universe[:10])
    top2 = pick_top2(universe)

    if len(top2) < 2:
        print("Could not find 2 top performers today (not enough data).")
        return

    print("Top 2 performers:", top2)

    # 3) Buy top 2
    for sym in top2:
        broker.buy_dollars(sym, DAILY_DOLLARS)

    print("DONE.")
    mark_ran_now()



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", repr(e))
        raise
