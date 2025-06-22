from src.backtester import Order
from typing import List, Dict
from collections import deque
import statistics

class Trader:
    def __init__(self):
        self.mid_price_history = {
            p: deque(maxlen=500) for p in ["ABRA", "SUDOWOODO", "DROWZEE"]
        }
        self.spread_AB_DZ = deque(maxlen=300)
        self.spread_DZ_SW = deque(maxlen=300)
        self.trade_flow = {
            p: deque(maxlen=30) for p in ["ABRA", "SUDOWOODO", "DROWZEE"]
        }
        self.max_position = 60
        self.ladder_levels = 3
        self.base_size = 4
        self.total_pnl = 0
        self.profit_target = 50000
        self.stop_trading = False

    def run(self, state) -> Dict[str, List[Order]]:
        result = {}
        pnl_change = 0.0

        mids = {}
        for product in self.mid_price_history:
            od = state.order_depth.get(product, {})
            if not od.buy_orders or not od.sell_orders:
                continue
            best_bid = max(od.buy_orders)
            best_ask = min(od.sell_orders)
            mid = (best_bid + best_ask) / 2
            mids[product] = mid
            self.mid_price_history[product].append(mid)

            pos = getattr(state, "position", {}).get(product, 0)
            if len(self.mid_price_history[product]) > 1:
                prev = self.mid_price_history[product][-2]
                pnl_change += (mid - prev) * pos

            trades = getattr(state, "market_trades", {}).get(product, [])
            net_flow = 0
            for t in trades:
                if t["price"] > mid:
                    net_flow += t["quantity"]
                elif t["price"] < mid:
                    net_flow -= t["quantity"]
            self.trade_flow[product].append(net_flow)

        self.total_pnl += pnl_change
        if self.total_pnl >= self.profit_target:
            self.stop_trading = True

        positions = getattr(state, "position", {})

        # === Double Pairs Arbitrage ===
        spread_AB_DZ = mids["ABRA"] - mids["DROWZEE"]
        spread_DZ_SW = mids["DROWZEE"] - mids["SUDOWOODO"]

        self.spread_AB_DZ.append(spread_AB_DZ)
        self.spread_DZ_SW.append(spread_DZ_SW)

        orders_ABRA, orders_DROWZEE, orders_SUDOWOODO = [], [], []

        if len(self.spread_AB_DZ) > 50:
            mean_AB_DZ = statistics.mean(self.spread_AB_DZ)
            stdev_AB_DZ = statistics.stdev(self.spread_AB_DZ) or 1e-6
            z_AB_DZ = (spread_AB_DZ - mean_AB_DZ) / stdev_AB_DZ

            mean_DZ_SW = statistics.mean(self.spread_DZ_SW)
            stdev_DZ_SW = statistics.stdev(self.spread_DZ_SW) or 1e-6
            z_DZ_SW = (spread_DZ_SW - mean_DZ_SW) / stdev_DZ_SW

            # === Pairs 1: ABRA vs DROWZEE
            if abs(z_AB_DZ) > 1.2:
                arb_size = 5
                if z_AB_DZ > 1.2:
                    orders_ABRA.append(Order("ABRA", mids["ABRA"], -arb_size))
                    orders_DROWZEE.append(Order("DROWZEE", mids["DROWZEE"], arb_size))
                elif z_AB_DZ < -1.2:
                    orders_ABRA.append(Order("ABRA", mids["ABRA"], arb_size))
                    orders_DROWZEE.append(Order("DROWZEE", mids["DROWZEE"], -arb_size))
            # === Pairs 2: DROWZEE vs SUDOWOODO
            if abs(z_DZ_SW) > 1.2:
                arb_size = 5
                if z_DZ_SW > 1.2:
                    orders_DROWZEE.append(Order("DROWZEE", mids["DROWZEE"], -arb_size))
                    orders_SUDOWOODO.append(Order("SUDOWOODO", mids["SUDOWOODO"], arb_size))
                elif z_DZ_SW < -1.2:
                    orders_DROWZEE.append(Order("DROWZEE", mids["DROWZEE"], arb_size))
                    orders_SUDOWOODO.append(Order("SUDOWOODO", mids["SUDOWOODO"], -arb_size))

            # === Triangular flatten: when both pair spreads normalize, flatten all legs
            if abs(z_AB_DZ) < 0.5 and abs(z_DZ_SW) < 0.5:
                pA = positions.get("ABRA", 0)
                pD = positions.get("DROWZEE", 0)
                pS = positions.get("SUDOWOODO", 0)
                if abs(pA) > 0:
                    orders_ABRA.append(Order("ABRA", mids["ABRA"], -pA))
                if abs(pD) > 0:
                    orders_DROWZEE.append(Order("DROWZEE", mids["DROWZEE"], -pD))
                if abs(pS) > 0:
                    orders_SUDOWOODO.append(Order("SUDOWOODO", mids["SUDOWOODO"], -pS))

        # === Ladder MM + Skew ===
        for product in ["ABRA", "DROWZEE", "SUDOWOODO"]:
            orders = []
            od = state.order_depth.get(product, {})
            if not od.buy_orders or not od.sell_orders:
                result[product] = orders
                continue

            mid = mids[product]
            pos = positions.get(product, 0)
            prices = list(self.mid_price_history[product])
            if len(prices) < 50:
                result[product] = orders
                continue

            mean = statistics.mean(prices[-50:])
            stdev = statistics.stdev(prices[-50:]) or 1e-6
            z = (mid - mean) / stdev
            flow = sum(self.trade_flow[product]) / (sum(abs(x) for x in self.trade_flow[product]) + 1e-6)
            trend = prices[-1] - prices[-50]
            trend_strength = trend / (50 * stdev + 1e-6)

            skew = max(-3, min(3, -z * 0.3 + flow * 1.5 + trend_strength * 3))
            ladder_levels = self.ladder_levels + (1 if stdev < 0.5 else 0)
            size = int(self.base_size + max(0, 4 - stdev * 50))
            size = min(size, 12)

            for level in range(1, ladder_levels + 1):
                step = level * 0.1 * stdev + 0.1
                bid_price = int(mid - step + skew)
                ask_price = int(mid + step + skew)
                if pos < self.max_position:
                    orders.append(Order(product, bid_price, size))
                if pos > -self.max_position:
                    orders.append(Order(product, ask_price, -size))

            if self.stop_trading:
                if pos > 0:
                    orders.append(Order(product, mid, -pos))
                elif pos < 0:
                    orders.append(Order(product, mid, -pos))

            if product == "ABRA":
                orders += orders_ABRA
            if product == "DROWZEE":
                orders += orders_DROWZEE
            if product == "SUDOWOODO":
                orders += orders_SUDOWOODO

            result[product] = orders

        return result
