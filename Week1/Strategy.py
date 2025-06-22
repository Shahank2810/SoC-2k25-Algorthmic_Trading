# Do not remove this line
from src.backtester import Order
import numpy as np
from collections import deque

class Trader:
    '''
    Advanced trading strategy combining:
    1. Mean Reversion
    2. Bollinger Bands
    3. RSI (Relative Strength Index)
    
    INPUT:
        - state: holds information about market trades, timestamps, position etc.
    OUTPUT:
        - results: Dict{"PRODUCT_NAME": List[Order]}
    '''
    
    def __init__(self):
        # Price history for calculations
        self.price_history = deque(maxlen=100)  # Keep last 100 prices
        self.volume_history = deque(maxlen=50)  # For volume analysis
        
        # Strategy parameters
        self.bb_period = 20  # Bollinger Bands period
        self.bb_std_dev = 2  # Standard deviations for BB
        self.rsi_period = 14
        self.mean_reversion_period = 20
        
        # Position management
        self.position_size = 10
        self.max_position = 100
        
        # Signal thresholds
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_moderate_oversold = 40
        self.rsi_moderate_overbought = 60
        
        # Mean reversion thresholds
        self.strong_reversion_threshold = 2.0  # Z-score threshold
        self.moderate_reversion_threshold = 1.0
        
        # Performance tracking
        self.trade_history = deque(maxlen=50)
        self.last_action = "hold"
        self.last_price = None
        
    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None, None, None
        
        prices_array = np.array(list(prices)[-period:])
        sma = np.mean(prices_array)
        std = np.std(prices_array)
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, sma, lower_band
    
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
            
        # Use exponential moving average for smoother RSI
        gains_recent = gains[-period:]
        losses_recent = losses[-period:]
        
        avg_gain = np.mean(gains_recent)
        avg_loss = np.mean(losses_recent)
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_mean_reversion_signal(self, current_price, sma=None):
        """Calculate mean reversion signal using price history"""
        if len(self.price_history) < self.mean_reversion_period:
            return 0, 0
        
        prices = list(self.price_history)
        
        # Use Bollinger Bands middle line as mean if available, otherwise calculate own mean
        if sma is not None:
            mean_price = sma
        else:
            mean_price = np.mean(prices[-self.mean_reversion_period:])
        
        std_price = np.std(prices[-self.mean_reversion_period:])
        
        if std_price == 0:
            return 0, mean_price
            
        z_score = (current_price - mean_price) / std_price
        return z_score, mean_price
    
    def calculate_bollinger_position(self, current_price, upper_band, lower_band, sma):
        """Calculate position relative to Bollinger Bands"""
        if upper_band is None or lower_band is None:
            return 0.5, 0  # Neutral position
        
        band_width = upper_band - lower_band
        if band_width == 0:
            return 0.5, 0
        
        # Position within bands (0 = lower band, 1 = upper band)
        bb_position = (current_price - lower_band) / band_width
        
        # Distance from middle line as percentage of band width
        distance_from_sma = (current_price - sma) / (band_width / 2)
        
        return bb_position, distance_from_sma
    
    def get_volume_signal(self):
        """Simple volume analysis"""
        if len(self.volume_history) < 5:
            return 1.0  # Neutral volume multiplier
        
        recent_volume = np.mean(list(self.volume_history)[-3:])
        avg_volume = np.mean(list(self.volume_history))
        
        # Higher volume = stronger signal confidence
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        return min(volume_ratio, 2.0)  # Cap at 2x
    
    def get_current_price(self, state):
        """Extract current price from state"""
        if hasattr(state, 'market_trades') and state.market_trades:
            return state.market_trades[-1].price
        elif hasattr(state, 'price'):
            return state.price
        elif hasattr(state, 'mid_price'):
            return state.mid_price
        else:
            # Fallback: use timestamp as proxy for price (for testing)
            return 10000 + (state.timestamp % 100)
    
    def get_volume(self, state):
        """Extract volume from state"""
        if hasattr(state, 'market_trades') and state.market_trades:
            return state.market_trades[-1].quantity
        elif hasattr(state, 'volume'):
            return state.volume
        else:
            return 1  # Default volume
    
    def calculate_adaptive_position_size(self, signal_strength, volatility):
        """Calculate position size based on signal strength and volatility"""
        base_size = self.position_size
        
        # Adjust for signal strength
        size_multiplier = min(abs(signal_strength), 2.0)
        
        # Adjust for volatility (lower volatility = larger positions)
        volatility_factor = 1.0 / (1.0 + volatility) if volatility > 0 else 1.0
        
        adjusted_size = int(base_size * size_multiplier * volatility_factor)
        return max(1, min(adjusted_size, self.position_size * 2))
    
    def run(self, state):
        results = {}
        orders = []
        
        # Get current market data
        current_price = self.get_current_price(state)
        current_volume = self.get_volume(state)
        
        # Update histories
        self.price_history.append(current_price)
        self.volume_history.append(current_volume)
        
        # Calculate all indicators
        upper_band, sma, lower_band = self.calculate_bollinger_bands(
            self.price_history, self.bb_period, self.bb_std_dev
        )
        rsi = self.calculate_rsi(self.price_history, self.rsi_period)
        z_score, mean_price = self.calculate_mean_reversion_signal(current_price, sma)
        
        # Get current position
        current_position = getattr(state, 'position', {}).get("PRODUCT", 0)
        
        # Skip if not enough data
        if upper_band is None or lower_band is None:
            results["PRODUCT"] = orders
            return results
        
        # Calculate Bollinger Bands position
        bb_position, distance_from_sma = self.calculate_bollinger_position(
            current_price, upper_band, lower_band, sma
        )
        
        # Generate signals
        
        # 1. Bollinger Bands signals
        bb_signal = 0
        if current_price <= lower_band:  # At or below lower band
            bb_signal = 1.0  # Strong buy
        elif current_price < lower_band + (upper_band - lower_band) * 0.2:  # Near lower band
            bb_signal = 0.5  # Moderate buy
        elif current_price >= upper_band:  # At or above upper band
            bb_signal = -1.0  # Strong sell
        elif current_price > upper_band - (upper_band - lower_band) * 0.2:  # Near upper band
            bb_signal = -0.5  # Moderate sell
        
        # 2. RSI signals
        rsi_signal = 0
        if rsi <= self.rsi_oversold:
            rsi_signal = 1.0  # Strong buy
        elif rsi <= self.rsi_moderate_oversold:
            rsi_signal = 0.5  # Moderate buy
        elif rsi >= self.rsi_overbought:
            rsi_signal = -1.0  # Strong sell
        elif rsi >= self.rsi_moderate_overbought:
            rsi_signal = -0.5  # Moderate sell
        
        # 3. Mean reversion signal
        mean_reversion_signal = 0
        if abs(z_score) >= self.strong_reversion_threshold:
            mean_reversion_signal = -1.0 if z_score > 0 else 1.0  # Strong contrarian
        elif abs(z_score) >= self.moderate_reversion_threshold:
            mean_reversion_signal = -0.5 if z_score > 0 else 0.5  # Moderate contrarian
        
        # Combine signals with weights
        # Bollinger Bands: 40%, RSI: 35%, Mean Reversion: 25%
        combined_signal = (bb_signal * 0.4 + rsi_signal * 0.35 + mean_reversion_signal * 0.25)
        
        # Volume confirmation
        volume_multiplier = self.get_volume_signal()
        final_signal = combined_signal * volume_multiplier
        
        # Calculate volatility for position sizing
        if len(self.price_history) >= 10:
            recent_prices = list(self.price_history)[-10:]
            volatility = np.std(recent_prices) / np.mean(recent_prices)
        else:
            volatility = 0.01
        
        # Generate orders based on final signal
        action_taken = "hold"
        
        if final_signal > 0.6 and current_position < self.max_position:
            # Strong buy signal
            quantity = self.calculate_adaptive_position_size(final_signal, volatility)
            quantity = min(quantity, self.max_position - current_position)
            
            if quantity > 0:
                # Price improvement: buy slightly below current price
                buy_price = int(current_price - max(1, int((upper_band - lower_band) * 0.001)))
                orders.append(Order("PRODUCT", buy_price, quantity))
                action_taken = "buy"
        
        elif final_signal > 0.3 and current_position < self.max_position:
            # Moderate buy signal
            quantity = self.calculate_adaptive_position_size(final_signal * 0.7, volatility)
            quantity = min(quantity, self.max_position - current_position)
            
            if quantity > 0:
                buy_price = int(current_price - 1)
                orders.append(Order("PRODUCT", buy_price, quantity))
                action_taken = "buy"
        
        elif final_signal < -0.6 and current_position > -self.max_position:
            # Strong sell signal
            quantity = self.calculate_adaptive_position_size(abs(final_signal), volatility)
            quantity = min(quantity, self.max_position + current_position)
            
            if quantity > 0:
                # Price improvement: sell slightly above current price
                sell_price = int(current_price + max(1, int((upper_band - lower_band) * 0.001)))
                orders.append(Order("PRODUCT", sell_price, -quantity))
                action_taken = "sell"
        
        elif final_signal < -0.3 and current_position > -self.max_position:
            # Moderate sell signal
            quantity = self.calculate_adaptive_position_size(abs(final_signal) * 0.7, volatility)
            quantity = min(quantity, self.max_position + current_position)
            
            if quantity > 0:
                sell_price = int(current_price + 1)
                orders.append(Order("PRODUCT", sell_price, -quantity))
                action_taken = "sell"
        
        # Track performance for future improvements
        if self.last_price is not None and self.last_action != "hold":
            price_change = current_price - self.last_price
            trade_result = {
                'action': self.last_action,
                'price_change': price_change,
                'profit': price_change if self.last_action == "buy" else -price_change
            }
            self.trade_history.append(trade_result)
        
        # Update tracking variables
        self.last_action = action_taken
        self.last_price = current_price
        
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
