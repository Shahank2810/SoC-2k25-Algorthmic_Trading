Before we actually get into the code, it’s worth looking into why algorithmic trading is so popular. Did you know that by 2019 about 92% of forex volume was traded by algorithms? If you don’t know what forex is, basically we buy and sell currencies instead of stocks (there’s more to it so you can read about it [here](https://www.investopedia.com/terms/f/forex.asp).) 

Algorithmic trading has its very important reasons for its fame:

- Traders exploit the **speed** and **precision** of computers to react to market moves faster than humans.
- Algorithms can trade continuously.
- Avoid human/emotional error because algorithms are purely mathematical and statistical, they are backtested on historical data.

But like everything else that sounds too good to be true, it has its limits:

- **Black Swan Events** can shock markets and break algorithms built upon rigid rules resulting in massive losses. Black swan events are those that come as a surprise (all of a sudden, without warning) even if you may have expected them. They are unpredictable. E.g. COVID-19
- Limited by technology as they require a lot of infrastructure to work fast.
- Strict regulatory rules apply to algorithmic trading which do not allow some optimal strategies to be deployed. For example, traders have to ensure that they implement pre-trade risk controls like position limits to protect against sudden big losses. In India, SEBI has OTR (order-to-trade ratio) limits and penalties for breaking these limits. This is all done to protect the investors. If you’re really interested in regulatory information, then read [here](https://www.marketfeed.com/read/en/what-are-sebis-key-regulations-on-algo-trading).
- Profit is not guaranteed. If you’ve heard somewhere that hedge funds always profit, then please clear your misinformation [here](https://www.ubs.com/global/en/assetmanagement/insights/asset-class-perspectives/hedge-funds/articles/uga-hf-bulletin-feb-2025.html).

Algo trading is great but it’s no magic money-making machine. It’s a great tool to diversify your capital and reduce risk, the profits show up over time. It’s mostly used by investment banks, hedge funds and some individual quants who have the resources. You’re here because of your interest in quant finance and building a good foundation. So read on to learn about actual strategies!
# Stratagies
## Mean Revision
  ### Intuition

Mean-reversion is the idea that prices tend to “bounce back” toward their historical average. They ‘revert’ back to their mean, hence the name. 

When a stock runs unusually high or low relative to its historical mean, the trader bets that it will return closer to average. This works well for stocks that are bounded by some range and are not highly volatile. Think **sideways** markets. 

(Volatility is approximately the same as standard deviation of the stock price (or returns), it can be calculated using various formulae, but both describe the same statistical property of the stock)

For example, a stable consumer stock that usually **swings** between $48 and $52 is a prime candidate. If it spikes to $57 (well above its usual range), a trader might **short** it expecting a **pullback**, and vice versa if it dips way below the mean. Graphically, you’d see the price oscillating around a horizontal band, sometimes touching “**support**” or “**resistance**” levels.

![image.png](attachment:eb901e3b-5b2a-42e5-8bc2-679487be5394:image.png)

Image is by [OptionAlpha](https://optionalpha.com/learn/mean-reversion) and very clearly explains what support and resistance bands are. Of course, the real charts aren’t this simple and both the support and resistance bands move as the market moves. We may employ short term averages and mean revert in these short intervals if the stock appears to be *slightly* volatile (slightly is a vague term but bear with it for now). We won’t be giving away everything, a lot of information is for you to look up and implement in your code. 

### Code

```python
mean_price = prices[-20:].mean()
threshold = 1.05
if current_price > mean_price * threshold:
    action = "sell_short"
elif current_price < mean_price / threshold:
    action = "buy"
else:
    action = "hold"
```

The pseudocode may appear too simple but there’s something important to learn here. In particular about the threshold and the number ‘20’. These are parameters that you optimize during backtesting. Threshold is self-explanatory but ‘20’ can mean a lot of different things like 20 seconds, minutes, hours, days, weeks, etc., depending on the asset, market and your algorithm. This is your **lookback** period to calculate the average on and make decisions. 

It’s not smart to have a constant threshold like the one in the pseudocode above. Can you guess why? Mean reversion combines with **Bollinger bands**, **RSI** and **Z-scores** to have thresholds that change with market conditions. We have written about them in a different page so close this section, scroll down and check it out.

### Further Reading

[IG International](https://www.ig.com/en/trading-strategies/what-is-mean-reversion-and-how-does-it-work--230605)
## Market Making
  ### Intuition

Buy low, sell high and keep doing it, both at the same time! The simplest strategy is market-making or MM. The trader tries to earn the **bid-ask spread** by offering to buy at some price and selling at a slightly higher price. If they do a lot of these trades (think 1000s), the profit becomes significantly large. This strategy is effective only in **highly liquid** markets. While there may be some market makers in low liquidity markets, they have to widen their spreads to reduce risk. 

Market makers are usually the big dogs in the game like Citadel, Goldman Sachs, JPMorgan Chase, and Morgan Stanley. They have the resources to provide continuous liquidity across various markets. According to law, registered market-makers are obligated to keep quoting bids and asks, their compensation for providing the market with liquidity is the profit earned from the spread. A question for you, if these traders earn their profit from the spread that they themselves create, why can’t they make it as large as possible? 

### Code

```python
mid_price = (best_bid + best_ask) / 2
spread = best_ask - best_bid
if spread > min_desired_spread:
    buy_price = mid_price - spread/2
    sell_price = mid_price + spread/2
    place_limit_order("buy", price=buy_price, amount=lot_size)
    place_limit_order("sell", price=sell_price, amount=lot_size)
```

The **best bid** is the highest price someone’s willing to buy your share at and the **best ask** is the lowest price someone’s willing to sell their share to you. **Mid-price** is the average of the two and we take it to be the **fair value** of the asset. Our buy orders will be placed at a price slightly lower than the mid-price and our sell orders will be placed slightly higher than the mid-price. You can play around with how much higher or lower you set your orders. 

It isn’t the best idea to blindly place a lot of orders. Market makers must have a good **inventory management** system in place so that they don’t accumulate large positions because the market could move against them and cause massive losses. We’ll explore this idea later.

### Further Reading

[Empirica](https://empirica.io/blog/market-making-strategy/)
## Stop Loss and Take Profit
    ### Mechanism

These aren’t ‘trading strategies’ in the manner we’ve been using the term, they are rules to manage **exits**. A **stop-loss** is an order that automatically closes your position if the price moves too much against you. A **take-profit** closes the position once it hits a target gain. Together they manage risk without constant monitoring. For example, if you buy a stock at $100 expecting it to go up, you might set a stop-loss at $95 to cap losses, and a take-profit at $110 to secure a 10% gain. On a chart, these would be horizontal lines on the top and bottom of your entry point; if price touches them, the trade ends.

### Code

```python
entry_price = purchase_price
stop_loss = entry_price * 0.9   # 10% drop
take_profit = entry_price * 1.2 # 20% rise

if current_price <= stop_loss:
    action = "sell_and_stop_loss"
elif current_price >= take_profit:
    action = "sell_and_take_profit"
else:
    action = "hold"
```

Very simple right? 

Question for you, why do we need a take-profit? Why can’t we remove it and collect as much profit as possible? 

Stop-loss thresholds are determined by backtesting your algorithm. It cannot be too tight because then it’ll detect noise and exit your position, and it can’t be too high, or you’ll suffer bigger losses before exiting a bad position. We want to stay in a profitable position for as long as possible and we want to exit a bad position as quickly as possible without getting distracted by noise. 

Try experimenting with dynamic stop-loss thresholds.
## Bollinger Bands
  ### Mechanism

If you haven’t read the mean-reversion section yet, do that first. Bollinger bands are directly connected to mean reversion but not exclusively. They are a volatility-based technical indicator consisting of three lines plotted around a price chart. The middle band is usually a 20-day simple moving average (SMA), and the upper and lower bands are found by adding and subtracting two standard deviations from the middle band. According to gaussian distribution, these bands should account for 95% of the price action, which leaves room for error — one of the reasons why we use additional indicators along with Bollinger bands. 

Logic behind this indicator is that as volatility increases (standard deviation increases), the Bollinger bands expand and vice versa if volatility is low. These bands serve as thresholds for mean reversion, for example, when the price touches the upper band, it signals a potential reversal in trend and traders short. It is very important to note that the price touching the upper band is not a **guarantee** of trend reversal. 

Which brings us to the limits of Bollinger bands. During strong **uptrends** or **downtrends**, the price could stay out of these bands for extended periods, therefore, Bollinger bands are only useful in range-bound and **sideways** markets. 

### Code

```python
def calculate_bollinger_bands(prices, period=20, std_multiplier=2.0):
    # Assume you defined a SMA function somewhere
    middle_band = SMA(prices, period)
    
    # Calculate standard deviation
    std_deviation = np.std(prices[-period:], ddof=1)
    
    # Calculate upper and lower bands
    upper_band = middle_band + (std_multiplier * std_deviation)
    lower_band = middle_band - (std_multiplier * std_deviation)
    
    return upper_band, middle_band, lower_band
```

We want you to look into why `np.std()` has the argument `ddof` and why we used it here. Also learn how to implement SMA in code yourself.

You can tune time period and the standard deviation multiplier for optimal bands.

### Further Reading

[Charles Schwab](https://www.schwab.com/learn/story/bollinger-bands-what-they-are-and-how-to-use-them)
## Relative Strength Index
  ### Mechanism

RSI is a momentum oscillator that measures the speed and magnitude of recent price changes. It measures momentum by comparing average gain and average losses over a period (typically 14 days) to determine if the stock is **overbought** or **oversold**. RSI gives an output between 0 and 100. Where 0 indicates oversold conditions and 100 indicates overbought. Look at the code below and it will clear all confusion. 

### Code

```python
def calculate_rsi(prices, period=14):
    gains = []
    losses = []
    
    # Calculate **daily** price changes
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0) # periods with price increase, we assume loss to be 0
        else:
            gains.append(0) # periods with price decrease, we assume profit to be 0
            losses.append(abs(change))
    
    # Calculate average gain and loss
    avg_gain = SMA(gains, period)
    avg_loss = SMA(losses, period)
    
    # Calculate RS and RSI
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
```

We used SMA here, but you might find traders using other averages which is fine, you can experiment with that. 

RSI + Bollinger bands form a good trading strategy for mean reversion or even trend following and volatile stocks (trend confirmation). RSI gives us the momentum signals and Bollinger bands provide the volatility information. Although, during strong trends, RSI can stay in overbought or oversold conditions for extended periods so you can’t just automatically decide everything based on RSI. It’s just one of the many indicators you can use.

From the code you should be able to understand what the RSI is but it's still not clear how we can use RSI. Try to think of what it means when RSI is 100 and when RSI is 0, what does that say for the `avg_gain` and `avg_loss` ? Typically, RSI above 70 is a strong signal that a stock is overbought and will show reversal, similarly RSI below 30 indicates oversold conditions.

If it’s still unclear, go on to the Further Reading section below and read the article.

### Further Reading

[Investopedia](https://www.investopedia.com/terms/r/rsi.asp)
## Momentum
  ### Intuition

“Ride the wave” is all it is. You see a strong upwards trend, ride it to the top and exit if it starts falling. Momentum traders have the idea that stocks which have been going up (or down) strongly, tend to continue in that direction for a while. In contrast to mean-reversion, momentum traders **buy high** and **sell higher**. 

To measure the momentum, you compare the current price to the price a certain number of time units (hours, days, weeks, etc.) ago. If the current price is significantly higher than it was a set period ago, you may go long; if it is significantly lower, you may go short. Traders develop their own strategies based on this principle. They use various statistical and technical indicators (such as moving averages, rate of change, or RSI) to quantify momentum, but the underlying concept remains as described.

> Example: Tech stocks during a **bull** market often have strong momentum. Suppose Company X’s stock has been climbing 5% each week for the past month. A momentum trader will realize there is a confirmed uptrend and ride the wave up. If the trend changes (the stock starts dropping instead), the trader might sell or short*.
> 

Remember that momentum traders don’t try to predict when an uptrend might begin, they only try to confirm if an uptrend has begun already and then ride the tide.

### Code

```python
lookback = 5
momentum = prices[-1] - prices[-1-lookback]
if momentum > 0:
    action = "buy"   # price is higher than 'lookback' time units ago
else:
    action = "sell"  # price is lower, downtrend may continue
```

You can think of using RSI here but this simple way of capturing momentum by comparing prices ‘lookback’ time units ago also works.

*There is difference between selling and shorting. Find out what it is.
## Z-score
  ### Mechanism

Z-score is an indicator of price extremes and can be used with mean reversion strategies. It has a pretty simple and standard formula given below:

### Code

```python
def calculate_zscore(prices, window=20):
    moving_avg = SMA(prices, window)
    moving_std = np.std(prices[-window:], ddof=1)
    zscore = (prices - moving_avg) / moving_std
    return zscore
```

A positive z-score like 2 means that the price is running 2 standard deviations above the average price and may revert. A negative z-score is similar, price is running 2 standard deviations below the average and may revert. A z-score of 0 or close to 0 (like <0.3) means there are no significant price changes happening.

If you are paying attention, you’ll notice that `moving_avg` and `moving_std` are scalars while prices is a list. This will throw an error in python unless we use numpy lists. Learn about numpy broadcasting [here](https://numpy.org/doc/stable/user/basics.broadcasting.html). In fact, this is not even the correct way to find rolling z-score. That you have to figure out yourself. But what we have in the above code is not entirely useless. It is also a z-score but relative only to the latest window which you can use for real-time signals. Rolling z-scores are calculated for all windows and are used to backtest, you task is to write the code for it using Numpy or Pandas.
