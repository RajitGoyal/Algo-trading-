from typing import List
from src.backtester import Order, OrderBook

class Trader:
    def __init__(self):
        self.mid_prices = []
        self.short_window = 5
        self.long_window = 20

    def run(self, state):
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        if len(order_depth.buy_orders) > 0:
            best_bid = max(order_depth.buy_orders.keys())
        else:
            best_bid = 9995

        if len(order_depth.sell_orders) > 0:
            best_ask = min(order_depth.sell_orders.keys())
        else:
            best_ask = 10005

        mid_price = (best_bid + best_ask) // 2
        self.mid_prices.append(mid_price)

        if len(self.mid_prices) > self.long_window:
            self.mid_prices.pop(0)

        if len(self.mid_prices) < self.long_window:
            return {"PRODUCT3": []}  # not enough data yet

        short_avg = sum(self.mid_prices[-self.short_window:]) / self.short_window
        long_avg = sum(self.mid_prices) / self.long_window

        # Trend following logic
        if short_avg > long_avg:
            orders.append(Order("PRODUCT3", best_ask, 10))  # Buy into uptrend
        elif short_avg < long_avg:
            orders.append(Order("PRODUCT3", best_bid, -10))  # Sell into downtrend

        return {"PRODUCT3": orders}
