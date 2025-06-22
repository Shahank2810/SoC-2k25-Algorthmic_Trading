

---

## 📈 Algorithmic Trading in Python

This repository contains my work on building and experimenting with algorithmic trading strategies using Python. The goal was to understand how automated trading works in practice by simulating real-time orders and testing various strategies in a controlled, virtual environment.
This is the project page in [notion](https://alive-quit-dd2.notion.site/1f306653ae11804a9413cf5979318fc1?v=1f306653ae118025aaaa000cbcde5da4)
---

### 🎯 **Project Overview**

I wanted to explore how trading bots can be designed, tested, and refined using Python. To do this, I focused on writing reusable classes that handle the main parts of a trading system — like orders, trades, and the order book — and then used them to try out different trading ideas.

---

### ⚙️ **What I Implemented**

* **Object-Oriented Design**

  * `Order` — defines a basic buy/sell order.
  * `Trade` — records details of executed trades.
  * `OrderBook` — simulates how a real exchange matches orders.

* **Order Matching Logic**

  * Orders are first matched within my own simulated order book.
  * If no match is possible, they can interact with external simulated participants (bots).

* **Risk Controls**

  * Position limits to prevent overexposure.
  * Logic for stop loss and take profit where applicable.

* **Trading Strategies Tried**

  * Mean Reversion
  * Market Making
  * Momentum
  * Breakout
  * Z-Score Method
  * Stop Loss / Take Profit variations
  * Bollinger Bands
  * Relative Strength Index (RSI)

I mainly experimented with how these strategies behave under different market conditions and tried combining ideas to see what works better.


