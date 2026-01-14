# config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    key: str
    secret: str
    base_url: str
    max_trades_per_day: int = 5
    cooldown_days: int = 2
    top_n: int = 5
    bottom_n: int = 5
    trust_threshold_buy: float = 0.55
    trust_threshold_short: float = 0.45
    stop_loss_pct: float = 0.05

def get_config() -> Config:
    key = os.getenv("KEY")
    secret = os.getenv("SECRET")
    base_url = os.getenv("BASE_URL", "https://paper-api.alpaca.markets")

    if not key or not secret:
        raise RuntimeError("Missing KEY or SECRET in .env")

    return Config(
        key=key,
        secret=secret,
        base_url=base_url,
    )
