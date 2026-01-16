# broker.py
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class Broker:
    def __init__(self, key: str, secret: str, paper: bool = True):
        self.client = TradingClient(api_key=key, secret_key=secret, paper=paper)

    def buy_dollars(self, symbol: str, dollars: float):
        order = MarketOrderRequest(
            symbol=symbol,
            notional=float(dollars),
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        result = self.client.submit_order(order_data=order)
        print(f"[ALPACA] BUY ${dollars:.0f} {symbol} | status={getattr(result,'status','?')}")
        return result
