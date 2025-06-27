from typing import List, Dict
from src.backtester import Order, OrderBook

class Trader:
    def __init__(self):
        pass

    def run(self, state):
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        if len(order_depth.buy_orders) > 0:
            best_bid = max(order_depth.buy_orders.keys())
        else:
            best_bid = 9995  # fallback if no bids

        if len(order_depth.sell_orders) > 0:
            best_ask = min(order_depth.sell_orders.keys())
        else:
            best_ask = 10005  # fallback if no asks

        mid_price = (best_bid + best_ask) // 2

        # Market making: Buy just below mid, sell just above mid
        buy_price = mid_price - 1
        sell_price = mid_price + 1

        # Always keep small volume to stay within position limits
        orders.append(Order("PRODUCT1", buy_price, 10))
        orders.append(Order("PRODUCT1", sell_price, -10))

        return {"PRODUCT1": orders}
