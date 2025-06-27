from typing import List
from src.backtester import Order, OrderBook

class Trader:
    def __init__(self):
        self.recent_mid_prices = []
        self.window_size = 10

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
        self.recent_mid_prices.append(mid_price)

        if len(self.recent_mid_prices) > self.window_size:
            self.recent_mid_prices.pop(0)

        avg_price = sum(self.recent_mid_prices) // len(self.recent_mid_prices)

        # Mean reversion logic
        if mid_price < avg_price - 1:
            orders.append(Order("PRODUCT2", best_ask, 10))  # Buy low
        elif mid_price > avg_price + 1:
            orders.append(Order("PRODUCT2", best_bid, -10))  # Sell high

        return {"PRODUCT2": orders}
