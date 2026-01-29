# clean_universe.py
# Reads universe.txt, removes tickers that have no Yahoo Finance price data, writes universe_clean.txt

import time
import yfinance as yf

INPUT_FILE = "universe.txt"
OUTPUT_FILE = "universe_clean.txt"

def has_price_data(symbol: str) -> bool:
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        if hist is None or hist.empty:
            return False
        closes = hist["Close"].dropna()
        return len(closes) >= 2
    except Exception:
        return False

def main():
    # 1) Read + basic cleanup
    with open(INPUT_FILE, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    # remove duplicates
    tickers = sorted(set(tickers))

    good = []
    bad = []

    print("Total tickers:", len(tickers))
    print("Checking Yahoo data...")

    # 2) Validate tickers using Yahoo Finance
    for i, t in enumerate(tickers, start=1):
        ok = has_price_data(t)
        if ok:
            good.append(t)
        else:
            bad.append(t)
            print(f"REMOVED: {t} (no price data / delisted)")

        # tiny pause so Yahoo doesn't get mad
        if i % 25 == 0:
            time.sleep(1)

    # 3) Write cleaned universe
    with open(OUTPUT_FILE, "w") as f:
        for t in good:
            f.write(t + "\n")

    print("\nDONE ✅")
    print("Kept:", len(good))
    print("Removed:", len(bad))
    print("Saved to:", OUTPUT_FILE)

    # optional: save removed list too
    with open("removed_tickers.txt", "w") as f:
        for t in bad:
            f.write(t + "\n")

if __name__ == "__main__":
    main()
