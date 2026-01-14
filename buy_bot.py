from config import get_config
from broker import Broker
# everything else stays the same

cfg = get_config()
broker = Broker(cfg.key, cfg.secret, cfg.base_url)

# BUY
broker.buy(symbol, qty)

# SELL
broker.sell(symbol, qty)
