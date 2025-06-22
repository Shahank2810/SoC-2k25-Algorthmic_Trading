## Overview of the Backtester Code

### Order

```python
class Order:
    symbol: str
    price: int
    quantity: int
```

- A **negative** quantity is a **sell** order while a **positive** quantity is a **buy** order.
    - E.g. Order(”PRODUCT_NAME”, 1000, -10) is a **sell** order for “PRODUCT_NAME” at price $1000 and quantity 10.
- **Price**: You put this price based on whatever trading strategy you come up with. Will always be positive.
- **Symbol**: Holds the name of the product. For now, it is hardcoded for a single product, and you will write different Strategy.py files for different products.

### Trade

```python
class Trade:
    timestamp: int
    price: int
    quantity: int
```

- This is how orders are stored in the market. All trades belong to the `Trade` class. Your orders can be either matched with the orderbook (uncrossed) or market trades.
- For market trades, you will not know who is selling and who is buying but if your price matches those orders, you can join the order with the other counterparties. It is important to note that your orders will be first matched with the uncrossed orderbook before the market trades. (More on this in another section)

### OrderBook

```python
class OrderBook:
    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}

    def update_from_price_row(self, row):
        self.buy_orders.clear()
        self.sell_orders.clear()

        for i in range(1, 4):
            bp = int(row[f"bid_price_{i}"]) if row[f"bid_price_{i}"] else None
            bv = int(row[f"bid_volume_{i}"]) if row[f"bid_volume_{i}"] else 0
            if bp is not None:
                self.buy_orders[bp] = bv

            ap = int(row[f"ask_price_{i}"]) if row[f"ask_price_{i}"] else None
            av = int(row[f"ask_volume_{i}"]) if row[f"ask_volume_{i}"] else 0
            if ap is not None:
                self.sell_orders[ap] = av
```

- `buy_orders` and `sell_orders` : These are a dictionary that hold the price and volume for each order in the market as `Dict[price: int, volume: int]`. You can access these two find the best bid and best ask in the market at any point.
    - E.g. {12:-3, 11:-2} Means that there are orders at price level 12 with quantity -3 and 11 with quantity -2. Negative sign means that these are sell orders.
- At every timestamp there are at most 3 bids and 3 asks in the orderbook. These outstanding orders are uncrossed, which means that every price level at which there are buy orders should always be strictly lower than all the levels at which there are sell orders. If not, then there is a potential match between buy and sell orders, and a trade between the bots should have happened.
- All trades that happen between bots are given in `trades.csv`. These are called `market_trades` and you can join them only if your orders don’t get matched with the `OrderBook`.

## Order Matching

- If there are active orders from counterparties for the same product against which your orders can be matched, then your order will be (partially) executed right away (no latency). If no immediate or partial execution is possible, the remaining order quantity will be visible for the bots in the market, and it might be that one of them sees it as a good trading opportunity and will trade against it. If none of the bots decides to trade against the remaining order quantity, it is cancelled. All this will happen before the next timestamp.
- Orders placed by `Trader.run` at a given timestamp are matched against the orderbook and market trades of that timestamp. Orderbook takes priority, if an order can be filled completely using volume in the relevant orderbook, market trades are not considered. If not, the backtester matches your order against the timestamp's market trades. In this case the backtester assumes that for each trade, the **buyer and the seller** of the trade are willing to trade with you instead at the **trade's** **price** and **volume**. Market trades are matched at the price of your orders, e.g. if you place a sell order for €9 and there is a market trade for €10, the sell order is matched at €9.
- Limits are enforced for every order. If your position for a product exceeds the limit because of an order, that order will get cancelled. Position limits are currently +50 and -50.

## Position Limits

- Just like in the real world of trading, there are position limits, i.e. limits to the size of the position that the algorithm can trade into in a single product. These position limits are defined on a per-product basis, and refer to the absolute allowable position size. So for a hypothetical position limit of 10, the position can neither be greater than 10 (long) nor less than -10 (short).
    - For example, the position limit in product X is 30 and the current position is -5, then any aggregated buy order volume exceeding 30 - (-5) = 35 would result in an order rejection.

## Testing of your Algorithm

- You are given 10000 timestamps to backtest your strategies on. We will backtest your strategies on unseen 10000 timestamps and then report your final profits. So make sure you don’t hardcode or overfit your algorithms.
- When we introduce new assets in later weeks, we will share with you the previous week’s unseen data, so you have more data to work with and improve your algorithm upon.

## Example Algorithm

```python
from src.backtester import Order, OrderBook
from typing import List

class Trader:
    
    def run(self, state):
        result = {}
        
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth
        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < 10000:
                orders.append(Order("PRODUCT", best_ask, -best_ask_amount))

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > 10000:
                orders.append(Order("PRODUCT", best_bid, -best_bid_amount))
        
        result["PRODUCT"] = orders
        return result
```

- Using this example code, you should be able to understand how you can use orderbook to find the best bids and best asks to make more complex strategies.
- You can initialize a global variable like mid-price and then store mid-prices in it for strategies like mean-reversion. You must not use global variables for anything other than storing mid-prices, averages, etc., such as for hardcoding. Remember that we will be testing these strategies on unseen data so hardcoding and overfitting will never work.

## Supported Libraries

- You must use only the following libraries:
    - pandas
    - Numpy
    - statistics
    - math
    - typing
    - jsonpickle

## Still Lost?

Here’s how to get $21k profit on Product 1.  Here’s the [notebook](https://colab.research.google.com/drive/12MHxIPVv2isH8GfVk0es4FOUhGGx1L4u?usp=sharing).

Make a copy if you want to edit it.
