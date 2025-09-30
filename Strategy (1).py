"""
Strategy.py
Submission-ready trading strategies for the V2 backtester.
Provides strategies for six products and two indexes:
 - SUDOWOODO, DROWZEE, ABRA (example base products)
 - SHINX, LUXRAY, JOLTEON (new products with given position limits)
 - ASH (Index 1) and MISTY (Index 2)

Guidelines followed:
 - Uses only allowed libraries (pandas, numpy, statistics, math, typing, jsonpickle)
 - Strategies are deterministic given state/orderbook
 - Position limits are enforced per-product
 - Index strategies compute synthetic basket fair values from component mid-prices and trade on premium
"""

from typing import List, Dict
from dataclasses import dataclass
import math
import numpy as np

# Simplified Order and OrderBook datatypes compatible with the backtester interface
@dataclass
class Order:
    symbol: str
    price: int
    quantity: int

class OrderBook:
    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}

# Base class for strategies
class BaseStrategy:
    def __init__(self, product_name: str, max_position: int):
        self.product_name = product_name
        self.max_position = max_position
        # ticksize and default order size can be tuned
        self.tick = 2
        self.default_size = max(1, int(max_position/10))
    
    def _best_bid(self, orderbook: OrderBook):
        if not orderbook.buy_orders:
            return None
        return max(orderbook.buy_orders.keys())
    
    def _best_ask(self, orderbook: OrderBook):
        if not orderbook.sell_orders:
            return None
        return min(orderbook.sell_orders.keys())
    
    def _mid_price(self, orderbook: OrderBook):
        b = self._best_bid(orderbook)
        a = self._best_ask(orderbook)
        if b is None and a is None:
            return None
        if b is None:
            return a - self.tick
        if a is None:
            return b + self.tick
        return (a + b) // 2
    
    def _size_allowed(self, position: int, side: str):
        # side: 'buy' or 'sell'
        if side == 'buy':
            allowed = self.max_position - position
        else:
            allowed = self.max_position + position  # since position could be negative
        return max(0, allowed)
    
    def get_orders(self, state, orderbook: OrderBook, position: int) -> List[Order]:
        return []


# Simple example product strategies
class SudowoodoStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("SUDOWOODO", 50)
        # a simple anchored fair value (can be adapted during live/backtest)
        self.fair_value = 10000
    
    def get_orders(self, state, orderbook, position):
        orders = []
        fv = self.fair_value
        size = min(self.default_size, self._size_allowed(position, 'buy'))
        sell_size = min(self.default_size, self._size_allowed(position, 'sell'))
        # place small passive orders around fair value
        if size > 0:
            orders.append(Order(self.product_name, fv - self.tick, size))
        if sell_size > 0:
            orders.append(Order(self.product_name, fv + self.tick, -sell_size))
        return orders


class DrowzeeStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("DROWZEE", 50)
    
    def get_orders(self, state, orderbook, position):
        orders = []
        mid = self._mid_price(orderbook)
        if mid is None:
            return orders
        buy_size = min(self.default_size, self._size_allowed(position, 'buy'))
        sell_size = min(self.default_size, self._size_allowed(position, 'sell'))
        if buy_size>0:
            orders.append(Order(self.product_name, mid - self.tick, buy_size))
        if sell_size>0:
            orders.append(Order(self.product_name, mid + self.tick, -sell_size))
        return orders


class AbraStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("ABRA", 50)
    
    def get_orders(self, state, orderbook, position):
        orders = []
        mid = self._mid_price(orderbook)
        if mid is None:
            return orders
        # slightly more aggressive sizes if spreads are wide
        spread = 0
        b = self._best_bid(orderbook)
        a = self._best_ask(orderbook)
        if b is not None and a is not None:
            spread = a - b
        size = min(self.default_size + (spread // 5), self._size_allowed(position, 'buy'))
        sell_size = min(self.default_size + (spread // 5), self._size_allowed(position, 'sell'))
        if size>0:
            orders.append(Order(self.product_name, mid - self.tick, size))
        if sell_size>0:
            orders.append(Order(self.product_name, mid + self.tick, -sell_size))
        return orders


# New product strategies (SHINX, LUXRAY, JOLTEON)
class ShinxStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("SHINX", 60)
        self.tick = 1
        self.default_size = 3
    
    def get_orders(self, state, orderbook, position):
        orders = []
        mid = self._mid_price(orderbook)
        if mid is None:
            return orders
        buy_allowed = self._size_allowed(position, 'buy')
        sell_allowed = self._size_allowed(position, 'sell')
        # tight market making for SHINX
        if buy_allowed > 0:
            orders.append(Order(self.product_name, mid - self.tick, min(self.default_size, buy_allowed)))
        if sell_allowed > 0:
            orders.append(Order(self.product_name, mid + self.tick, -min(self.default_size, sell_allowed)))
        return orders


class LuxrayStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("LUXRAY", 250)
        self.tick = 3
        self.default_size = 8
    
    def get_orders(self, state, orderbook, position):
        orders = []
        mid = self._mid_price(orderbook)
        if mid is None:
            return orders
        # slightly larger sizes as Luxray has a larger position limit
        buy_allowed = self._size_allowed(position, 'buy')
        sell_allowed = self._size_allowed(position, 'sell')
        if buy_allowed > 0:
            orders.append(Order(self.product_name, mid - self.tick, min(self.default_size, buy_allowed)))
        if sell_allowed > 0:
            orders.append(Order(self.product_name, mid + self.tick, -min(self.default_size, sell_allowed)))
        return orders


class JolteonStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("JOLTEON", 350)
        self.tick = 4
        self.default_size = 10
    
    def get_orders(self, state, orderbook, position):
        orders = []
        mid = self._mid_price(orderbook)
        if mid is None:
            return orders
        buy_allowed = self._size_allowed(position, 'buy')
        sell_allowed = self._size_allowed(position, 'sell')
        # market-making with moderately larger sizes
        if buy_allowed > 0:
            orders.append(Order(self.product_name, mid - self.tick, min(self.default_size, buy_allowed)))
        if sell_allowed > 0:
            orders.append(Order(self.product_name, mid + self.tick, -min(self.default_size, sell_allowed)))
        return orders


# Index strategies: trade index vs synthetic basket (basic premium-arbitrage)
class AshIndexStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("ASH", 60)  # Index position limit as provided
        # Index composition: 6 Luxrays, 3 Jolteons, 1 Shinx
        self.weights = {"LUXRAY": 6, "JOLTEON": 3, "SHINX": 1}
        self.tick = 5
        self.default_size = 2
    
    def _synthetic_price(self, state):
        # compute synthetic index price using component mid-prices
        mids = {}
        for p, ob in state.order_depth.items():
            if p in self.weights:
                b = None if not ob.buy_orders else max(ob.buy_orders.keys())
                a = None if not ob.sell_orders else min(ob.sell_orders.keys())
                if b is None and a is None:
                    return None  # cannot compute synthetic
                mid = (a + b) // 2 if (a is not None and b is not None) else (a - 1 if b is None else b + 1)
                mids[p] = mid
        if len(mids) != len(self.weights):
            return None
        syn = sum(mids[p] * w for p, w in self.weights.items())
        return syn
    
    def get_orders(self, state, orderbook, position):
        orders = []
        synthetic = self._synthetic_price(state)
        index_mid = self._mid_price(orderbook)
        if synthetic is None or index_mid is None:
            return orders
        premium = index_mid - synthetic
        # If index is trading at a premium, sell index and buy components (and vice-versa)
        size = min(self.default_size, self._size_allowed(position, 'sell' if premium>0 else 'buy'))
        if size <= 0:
            return orders
        if premium > self.tick:
            # sell index, buy components (we generate one side of the hedge here as orders)
            orders.append(Order(self.product_name, index_mid, -size))
            # create corresponding component buy orders (notional units scaled by weight)
            for p, w in self.weights.items():
                # we place constructive buys at component mid - 1 tick to fill
                ob = state.order_depth[p]
                mid = (max(ob.buy_orders.keys()) + min(ob.sell_orders.keys())) // 2 if ob.buy_orders and ob.sell_orders else None
                if mid is not None:
                    qty = min(w * size,  self._size_allowed(state.positions.get(p,0), 'buy'))
                    if qty>0:
                        orders.append(Order(p, mid - 1, qty))
        elif premium < -self.tick:
            # buy index, sell components
            orders.append(Order(self.product_name, index_mid, size))
            for p, w in self.weights.items():
                ob = state.order_depth[p]
                mid = (max(ob.buy_orders.keys()) + min(ob.sell_orders.keys())) // 2 if ob.buy_orders and ob.sell_orders else None
                if mid is not None:
                    qty = min(w * size,  self._size_allowed(state.positions.get(p,0), 'sell'))
                    if qty>0:
                        orders.append(Order(p, mid + 1, -qty))
        return orders


class MistyIndexStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("MISTY", 100)
        # Index composition: 4 Luxrays, 2 Jolteons
        self.weights = {"LUXRAY": 4, "JOLTEON": 2}
        self.tick = 5
        self.default_size = 3
    
    def _synthetic_price(self, state):
        mids = {}
        for p, ob in state.order_depth.items():
            if p in self.weights:
                b = None if not ob.buy_orders else max(ob.buy_orders.keys())
                a = None if not ob.sell_orders else min(ob.sell_orders.keys())
                if b is None and a is None:
                    return None
                mid = (a + b) // 2 if (a is not None and b is not None) else (a - 1 if b is None else b + 1)
                mids[p] = mid
        if len(mids) != len(self.weights):
            return None
        syn = sum(mids[p] * w for p, w in self.weights.items())
        return syn
    
    def get_orders(self, state, orderbook, position):
        orders = []
        synthetic = self._synthetic_price(state)
        index_mid = self._mid_price(orderbook)
        if synthetic is None or index_mid is None:
            return orders
        premium = index_mid - synthetic
        size = min(self.default_size, self._size_allowed(position, 'sell' if premium>0 else 'buy'))
        if size<=0:
            return orders
        if premium > self.tick:
            orders.append(Order(self.product_name, index_mid, -size))
            for p, w in self.weights.items():
                ob = state.order_depth[p]
                mid = (max(ob.buy_orders.keys()) + min(ob.sell_orders.keys())) // 2 if ob.buy_orders and ob.sell_orders else None
                if mid is not None:
                    qty = min(w * size, self._size_allowed(state.positions.get(p,0), 'buy'))
                    if qty>0:
                        orders.append(Order(p, mid - 1, qty))
        elif premium < -self.tick:
            orders.append(Order(self.product_name, index_mid, size))
            for p, w in self.weights.items():
                ob = state.order_depth[p]
                mid = (max(ob.buy_orders.keys()) + min(ob.sell_orders.keys())) // 2 if ob.buy_orders and ob.sell_orders else None
                if mid is not None:
                    qty = min(w * size, self._size_allowed(state.positions.get(p,0), 'sell'))
                    if qty>0:
                        orders.append(Order(p, mid + 1, -qty))
        return orders


# Trader wrapper to plug into the backtester
class Trader:
    def __init__(self):
        # Map product names used by the backtester to strategy instances
        self.strategies = {
            "SUDOWOODO": SudowoodoStrategy(),
            "DROWZEE": DrowzeeStrategy(),
            "ABRA": AbraStrategy(),
            "SHINX": ShinxStrategy(),
            "LUXRAY": LuxrayStrategy(),
            "JOLTEON": JolteonStrategy(),
            "ASH": AshIndexStrategy(),
            "MISTY": MistyIndexStrategy()
        }
    
    def run(self, state):
        result = {}
        positions = getattr(state, 'positions', {})
        for product, orderbook in state.order_depth.items():
            current_position = positions.get(product, 0)
            strat = self.strategies.get(product)
            if strat:
                product_orders = strat.get_orders(state, orderbook, current_position)
                result[product] = product_orders
            else:
                result[product] = []
        return result
