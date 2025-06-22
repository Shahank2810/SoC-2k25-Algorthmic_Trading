# Do not remove this line
# Do not remove this line
from src.backtester import Order
import numpy as np
from collections import deque

class Trader:
    '''
    Advanced trading strategy combining:
    1. Mean Reversion
    2. RSI (Relative Strength Index) 
    3. UCB (Upper Confidence Bound) with dynamic confidence
    
    INPUT:
        - state: holds information about market trades, timestamps, position etc.
    OUTPUT:
        - results: Dict{"PRODUCT_NAME": List[Order]}
    '''
    
    def __init__(self):
        # Price history for mean reversion and RSI calculation
        self.price_history = deque(maxlen=100)  # Keep last 100 prices
        self.returns_history = deque(maxlen=50)  # For volatility calculation
        
        # UCB parameters
        self.action_counts = {"buy": 0, "sell": 0, "hold": 0}
        self.action_rewards = {"buy": 0.0, "sell": 0.0, "hold": 0.0}
        self.total_actions = 0
        
        # Strategy parameters
        self.lookback_period = 20  # For mean reversion
        self.rsi_period = 14
        self.position_size = 10
        self.max_position = 100
        
        # Dynamic parameters
        self.volatility_lookback = 20
        
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI if not enough data
            
        prices = list(prices)
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
            
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_mean_reversion_signal(self, current_price):
        """Calculate mean reversion signal"""
        if len(self.price_history) < self.lookback_period:
            return 0, 0  # No signal if not enough data
            
        prices = list(self.price_history)
        mean_price = np.mean(prices[-self.lookback_period:])
        std_price = np.std(prices[-self.lookback_period:])
        
        if std_price == 0:
            return 0, mean_price
            
        z_score = (current_price - mean_price) / std_price
        return z_score, mean_price
    
    def calculate_dynamic_confidence(self):
        """Calculate dynamic confidence for UCB based on volatility"""
        if len(self.returns_history) < 2:
            return 1.0  # Default confidence
            
        returns = list(self.returns_history)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if abs(mean_return) < 1e-8:  # Avoid division by zero
            return 1.0 + std_return
        
        # Dynamic confidence: 1 + std/|mean|
        confidence = 1.0 + (std_return / abs(mean_return))
        return min(confidence, 5.0)  # Cap at 5.0 to avoid extreme values
    
    def calculate_ucb_values(self, dynamic_confidence):
        """Calculate UCB values for each action"""
        if self.total_actions == 0:
            return {"buy": float('inf'), "sell": float('inf'), "hold": float('inf')}
        
        ucb_values = {}
        for action in ["buy", "sell", "hold"]:
            if self.action_counts[action] == 0:
                ucb_values[action] = float('inf')
            else:
                avg_reward = self.action_rewards[action] / self.action_counts[action]
                exploration = dynamic_confidence * np.sqrt(
                    np.log(self.total_actions) / self.action_counts[action]
                )
                ucb_values[action] = avg_reward + exploration
        
        return ucb_values
    
    def update_ucb(self, action, reward):
        """Update UCB statistics"""
        self.action_counts[action] += 1
        self.action_rewards[action] += reward
        self.total_actions += 1
    
    def get_current_price(self, state):
        """Extract current price from state"""
        # Try different ways to get current price based on state structure
        if hasattr(state, 'market_trades') and state.market_trades:
            return state.market_trades[-1].price
        elif hasattr(state, 'price'):
            return state.price
        elif hasattr(state, 'mid_price'):
            return state.mid_price
        else:
            # Fallback: use timestamp as proxy for price (for testing)
            return 10000 + (state.timestamp % 100)
    
    def run(self, state):
        results = {}
        orders = []
        
        # Get current price
        current_price = self.get_current_price(state)
        
        # Update price history
        if len(self.price_history) > 0:
            last_price = self.price_history[-1]
            price_return = (current_price - last_price) / last_price
            self.returns_history.append(price_return)
        
        self.price_history.append(current_price)
        
        # Calculate indicators
        rsi = self.calculate_rsi(self.price_history, self.rsi_period)
        z_score, mean_price = self.calculate_mean_reversion_signal(current_price)
        dynamic_confidence = self.calculate_dynamic_confidence()
        ucb_values = self.calculate_ucb_values(dynamic_confidence)
        
        # Get current position
        current_position = getattr(state, 'position', {}).get("PRODUCT", 0)
        
        # Generate trading signals
        # Mean reversion signals
        mean_reversion_signal = 0
        if abs(z_score) > 1.5:  # Strong deviation from mean
            mean_reversion_signal = -1 if z_score > 0 else 1  # Contrarian
        elif abs(z_score) > 1.0:  # Moderate deviation
            mean_reversion_signal = -0.5 if z_score > 0 else 0.5
        
        # RSI signals
        rsi_signal = 0
        if rsi < 30:  # Oversold
            rsi_signal = 1
        elif rsi > 70:  # Overbought
            rsi_signal = -1
        elif rsi < 40:  # Moderately oversold
            rsi_signal = 0.5
        elif rsi > 60:  # Moderately overbought
            rsi_signal = -0.5
        
        # Combined signal strength
        combined_signal = (mean_reversion_signal + rsi_signal) / 2
        
        # UCB action selection
        best_action = max(ucb_values.keys(), key=lambda k: ucb_values[k])
        
        # Decision making with position limits
        action_taken = "hold"
        
        if combined_signal > 0.5 and current_position < self.max_position and best_action in ["buy", "hold"]:
            # Strong buy signal
            quantity = min(self.position_size * 2, self.max_position - current_position)
            if quantity > 0:
                buy_price = int(current_price - 2)  # Slightly below market
                orders.append(Order("PRODUCT", buy_price, quantity))
                action_taken = "buy"
        
        elif combined_signal > 0.2 and current_position < self.max_position and best_action != "sell":
            # Moderate buy signal
            quantity = min(self.position_size, self.max_position - current_position)
            if quantity > 0:
                buy_price = int(current_price - 1)
                orders.append(Order("PRODUCT", buy_price, quantity))
                action_taken = "buy"
        
        elif combined_signal < -0.5 and current_position > -self.max_position and best_action in ["sell", "hold"]:
            # Strong sell signal
            quantity = min(self.position_size * 2, self.max_position + current_position)
            if quantity > 0:
                sell_price = int(current_price + 2)  # Slightly above market
                orders.append(Order("PRODUCT", sell_price, -quantity))
                action_taken = "sell"
        
        elif combined_signal < -0.2 and current_position > -self.max_position and best_action != "buy":
            # Moderate sell signal
            quantity = min(self.position_size, self.max_position + current_position)
            if quantity > 0:
                sell_price = int(current_price + 1)
                orders.append(Order("PRODUCT", sell_price, -quantity))
                action_taken = "sell"
        
        # Calculate reward for UCB (simplified P&L estimation)
        if len(self.price_history) >= 2:
            price_change = current_price - self.price_history[-2]
            if action_taken == "buy":
                reward = price_change * 0.01  # Normalize reward
            elif action_taken == "sell":
                reward = -price_change * 0.01
            else:
                reward = -abs(price_change) * 0.001  # Small penalty for inaction during volatility
            
            self.update_ucb(action_taken, reward)
        
        results["PRODUCT"] = orders
        return results

    def run(self, state):
        
        results = {}
        orders = []

        # Hardcoded for now, you will decide this. This is not the optimal strategy
        buy_price = 9998
        sell_price = 10002

        if state.timestamp % 2 == 1:
            # Order("PRODUCT_NAME": str, price: int, quantity: int)
            orders.append(Order("PRODUCT", buy_price, 10)) # Positive quantity -> Buy order
        else:
            orders.append(Order("PRODUCT", sell_price, -10)) # Negative quantity -> Sell order

        results["PRODUCT"] = orders

        return results
