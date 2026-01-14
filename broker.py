# broker.py
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class Broker:
    def __init__(self, key: str, secret: str, base_url: str):
        self.client = TradingClient(
            api_key=key,
            secret_key=secret,
            paper=True  # change to False for live trading
        )

    def buy(self, symbol: str, qty: int):
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        self.client.submit_order(order)
        print(f"[ALPACA] BUY {qty} {symbol}")

    def sell(self, symbol: str, qty: int):
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        self.client.submit_order(order)
        print(f"[ALPACA] SELL {qty} {symbol}")

    def short(self, symbol: str, qty: int):
        # Alpaca shorts via SELL (margin account required)
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        self.client.submit_order(order)
        print(f"[ALPACA] SHORT {qty} {symbol}")

    def cover(self, symbol: str, qty: int):
        # Cover = BUY
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        self.client.submit_order(order)
        print(f"[ALPACA] COVER {qty} {symbol}")
