# daily_buyer.py
print("daily_buyer.py started")

import os
import math
from datetime import datetime, timezone, timedelta

import yfinance as yf
from broker import Broker

# -----------------------------
# CONFIG
# -----------------------------
PAPER = os.getenv("PAPER", "true").lower() == "true"

# Use env vars (GitHub Actions secrets) OR local .env (optional)
# If you still want local .env, keep python-dotenv and call load_dotenv() manually.
KEY = os.getenv("KEY")
SECRET = os.getenv("SECRET")

if not KEY or not SECRET:
    raise ValueError("Missing KEY/SECRET environment variables")

DAILY_DOLLARS = 500
ETF_LIST = ["VOO", "SPY"]
UNIVERSE_FILE = "universe_clean.txt"  # use your cleaned file if you made it

MAX_POSITIONS = 15                 # don’t hold more than this many names total
MAX_DOLLARS_PER_SYMBOL = 1500      # don’t keep stacking endlessly
BUY_TOP_N = 2

# If True: only allow the bot to place orders once per hour (works on GitHub Actions)
ENFORCE_HOURLY_LIMIT = True


# -----------------------------
# HELPERS
# -----------------------------
def load_universe() -> list[str]:
    with open(UNIVERSE_FILE, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    tickers = [t for t in tickers if t not in ETF_LIST]
    # dedupe
    tickers = sorted(set(tickers))
    return tickers


def has_open_order(client, symbol: str) -> bool:
    # Any accepted/new order for this symbol? Then skip to avoid duplicates.
    try:
        orders = client.get_orders()
        for o in orders:
            if o.symbol == symbol and str(o.status) in ("OrderStatus.ACCEPTED", "OrderStatus.NEW", "OrderStatus.PENDING_NEW"):
                return True
    except Exception:
        pass
    return False


def position_market_value_usd(client, symbol: str) -> float:
    try:
        positions = client.get_all_positions()
        for p in positions:
            if p.symbol == symbol:
                # Alpaca returns strings
                return float(getattr(p, "market_value", 0.0))
    except Exception:
        pass
    return 0.0


def count_positions(client) -> int:
    try:
        return len(client.get_all_positions())
    except Exception:
        return 0


def traded_within_last_hour(client) -> bool:
    """
    Best hourly lock for GitHub Actions: check Alpaca account activities.
    If we submitted any trades in the last 60 minutes, skip.
    """
    try:
        now = datetime.now(timezone.utc)
        since = now - timedelta(minutes=60)

        # alpaca-py supports get_activities, but the exact method name can vary by version.
        # We'll try a couple common patterns safely.
        activities = []
        if hasattr(client, "get_activities"):
            activities = client.get_activities(activity_types=["FILL", "ORDER"])
        elif hasattr(client, "get_account_activities"):
            activities = client.get_account_activities()

        for a in activities:
            # Try the common timestamp fields
            ts = None
            for field in ("transaction_time", "created_at", "timestamp", "time"):
                if hasattr(a, field):
                    ts = getattr(a, field)
                    break
            if not ts:
                continue

            # If it's a string, parse a bit loosely
            if isinstance(ts, str):
                try:
                    ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    continue
            else:
                ts_dt = ts

            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=timezone.utc)

            if ts_dt >= since:
                return True

    except Exception:
        # If activity call fails, don’t block trading—just proceed.
        return False

    return False


# -----------------------------
# TREND SCORE (better than 1-day % spike)
# -----------------------------
def trend_score(symbol: str) -> float | None:
    """
    Score stocks that are in a strong uptrend:
      - close > MA50 > MA200
    Score = weighted distance above MA50 and MA200.
    """
    try:
        hist = yf.Ticker(symbol).history(period="1y")  # enough for MA200
        if hist is None or hist.empty:
            return None

        close = hist["Close"].dropna()
        if len(close) < 210:
            return None

        last = float(close.iloc[-1])
        ma50 = float(close.tail(50).mean())
        ma200 = float(close.tail(200).mean())

        if not (last > ma50 > ma200):
            return None

        # simple trend strength score
        score = 0.6 * (last / ma50 - 1.0) + 0.4 * (last / ma200 - 1.0)

        # tiny penalty if last is extremely stretched above MA50 (reduces "spike chasing")
        stretch = (last / ma50 - 1.0)
        if stretch > 0.12:  # 12% above MA50 is kinda stretched
            score -= (stretch - 0.12) * 0.5

        if not math.isfinite(score):
            return None
        return score

    except Exception:
        return None


def pick_top_trends(tickers: list[str], n: int) -> list[str]:
    scored = []
    skipped = 0
    for t in tickers:
        s = trend_score(t)
        if s is None:
            skipped += 1
            continue
        scored.append((s, t))

    scored.sort(reverse=True, key=lambda x: x[0])
    picks = [t for _, t in scored[:n]]

    print("Trend candidates:", len(scored), "| skipped:", skipped)
    return picks


# -----------------------------
# MAIN
# -----------------------------
def main():
    print("INSIDE MAIN ✅")
    b = Broker(KEY, SECRET, paper=PAPER)

    if ENFORCE_HOURLY_LIMIT and traded_within_last_hour(b.client):
        print("Already traded within the last hour — skipping.")
        return

    acct = b.client.get_account()
    buying_power = float(acct.buying_power)

    planned_spend = DAILY_DOLLARS * (len(ETF_LIST) + BUY_TOP_N)
    print("MODE:", "PAPER" if PAPER else "LIVE")
    print("Buying power:", buying_power)
    print("Planned spend (max):", planned_spend)

    if planned_spend > buying_power:
        print("Not enough buying power. Stop.")
        return

    # Position cap
    current_positions = count_positions(b.client)
    if current_positions >= MAX_POSITIONS:
        print(f"Position cap reached ({current_positions}/{MAX_POSITIONS}). Skipping buys.")
        return

    # 1) Buy ETFs (skip if open order exists or too much already)
    for etf in ETF_LIST:
        if has_open_order(b.client, etf):
            print("Skipping", etf, "(already has open order)")
            continue
        if position_market_value_usd(b.client, etf) >= MAX_DOLLARS_PER_SYMBOL:
            print("Skipping", etf, f"(already >= ${MAX_DOLLARS_PER_SYMBOL})")
            continue
        b.buy_dollars(etf, DAILY_DOLLARS)

    # 2) Pick top trend names
    universe = load_universe()
    print("Universe size:", len(universe))
    top = pick_top_trends(universe, BUY_TOP_N)

    if len(top) < BUY_TOP_N:
        print("Not enough trend candidates today — skipping stock picks.")
        return

    print("Top trend picks:", top)

    # 3) Buy top picks (skip duplicates / caps)
    for sym in top:
        if has_open_order(b.client, sym):
            print("Skipping", sym, "(already has open order)")
            continue
        if position_market_value_usd(b.client, sym) >= MAX_DOLLARS_PER_SYMBOL:
            print("Skipping", sym, f"(already >= ${MAX_DOLLARS_PER_SYMBOL})")
            continue

        # Re-check position cap
        current_positions = count_positions(b.client)
        if current_positions >= MAX_POSITIONS:
            print(f"Position cap reached ({current_positions}/{MAX_POSITIONS}). Stop buying.")
            break

        b.buy_dollars(sym, DAILY_DOLLARS)

    print("DONE.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", repr(e))
        raise
