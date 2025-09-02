# strategies/vwap_reversion/trend_filter.py

import config
from datetime import datetime, time
from engine.state import SymbolState
from typing import Optional

class TrendFilter:
    """
    Implements trend detection using ADX and z-score persistence
    to avoid mean reversion trades during strong trending periods.
    """
    
    def __init__(self):
        self.ny_session_start = time(config.NY_SESSION_START_HOUR, config.NY_SESSION_START_MINUTE)
        self.ny_session_end = time(config.NY_SESSION_END_HOUR, config.NY_SESSION_END_MINUTE)
    
    def should_avoid_mean_reversion(self, state: SymbolState, z_score: float, 
                                  high_price: float, low_price: float, 
                                  current_price: float,
                                  timestamp: Optional[datetime] = None) -> bool:
        """
        Determine if mean reversion trading should be avoided due to trending conditions.
        
        Returns True if trend detected (avoid mean reversion), False otherwise.
        """
        # Only apply trend filter during NY session
        if timestamp and not self._is_ny_session(timestamp):
            return False
            
        # Update price momentum tracking
        price_momentum = self._update_price_momentum(state, current_price, timestamp)
        
        # Update ADX calculation
        current_adx = self._update_and_get_adx(state, high_price, low_price)
        
        # Update z-score persistence tracking
        is_persistent = self._update_z_score_persistence(state, z_score, timestamp)
        
        # Check for velocity-based trend
        high_velocity = self._check_price_velocity(state, current_price)
        
        # Check for momentum divergence (early trend warning)
        momentum_divergence = self._check_momentum_divergence(state, current_price, z_score)
        
        # Avoid mean reversion if any filter triggers
        adx_trending = current_adx and current_adx > config.ADX_TREND_THRESHOLD
        strong_momentum = abs(price_momentum) > getattr(config, 'MOMENTUM_THRESHOLD', 2.0)
        
        trend_detected = (adx_trending or is_persistent or high_velocity or 
                         strong_momentum or momentum_divergence)
        
        if trend_detected:
            return True
            
        return False
    
    def _is_ny_session(self, timestamp: datetime) -> bool:
        """Check if timestamp is within NY trading session (CT)"""
        current_time = timestamp.time()
        return self.ny_session_start <= current_time <= self.ny_session_end
    
    def _update_and_get_adx(self, state: SymbolState, high: float, low: float) -> Optional[float]:
        """
        Update ADX calculation with new high/low prices.
        Returns current ADX value or None if insufficient data.
        """
        # Store price data for ADX calculation
        state.high_prices.append(high)
        state.low_prices.append(low)
        
        # Keep only last ADX_PERIOD + 1 values (need n+1 for n differences)
        max_len = config.ADX_PERIOD + 1
        if len(state.high_prices) > max_len:
            state.high_prices = state.high_prices[-max_len:]
            state.low_prices = state.low_prices[-max_len:]
        
        # Need at least ADX_PERIOD + 1 observations for calculation
        if len(state.high_prices) < config.ADX_PERIOD + 1:
            return None
            
        return self._calculate_adx(state, state.high_prices, state.low_prices)
    
    def _calculate_adx(self, state: SymbolState, highs: list, lows: list) -> float:
        """
        Calculate ADX using simplified Wilder's method.
        ADX measures trend strength, not direction.
        """
        period = config.ADX_PERIOD
        
        # Calculate True Range and Directional Movement
        tr_values = []
        dm_plus = []
        dm_minus = []
        
        for i in range(1, len(highs)):
            # True Range components
            h_l = highs[i] - lows[i]
            h_pc = abs(highs[i] - highs[i-1])  # Using previous high as proxy for close
            l_pc = abs(lows[i] - lows[i-1])    # Using previous low as proxy for close
            tr = max(h_l, h_pc, l_pc)
            tr_values.append(tr)
            
            # Directional Movement
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            
            dm_plus.append(up_move if up_move > down_move and up_move > 0 else 0)
            dm_minus.append(down_move if down_move > up_move and down_move > 0 else 0)
        
        # Need at least 'period' values for smoothing
        if len(tr_values) < period:
            return 0.0
            
        # Calculate smoothed TR, DM+, and DM-
        atr = sum(tr_values[-period:]) / period
        adm_plus = sum(dm_plus[-period:]) / period
        adm_minus = sum(dm_minus[-period:]) / period
        
        # Calculate Directional Indicators
        if atr == 0:
            return 0.0
            
        di_plus = (adm_plus / atr) * 100
        di_minus = (adm_minus / atr) * 100
        
        # Calculate ADX
        dx = abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10) * 100
        
        # Store DX value for ADX smoothing
        state.adx_values.append(dx)
        
        # Keep only last 'period' DX values for ADX calculation
        if len(state.adx_values) > period:
            state.adx_values = state.adx_values[-period:]
            
        # ADX is the smoothed average of DX
        adx = sum(state.adx_values) / len(state.adx_values)
        
        return adx
    
    def _update_z_score_persistence(self, state: SymbolState, z_score: float, 
                                  timestamp: Optional[datetime]) -> bool:
        """
        Track how long z-score has been above threshold.
        Returns True if persistence indicates trend day.
        """
        abs_z_score = abs(z_score)
        
        # Check if z-score is above persistence threshold
        if abs_z_score > config.Z_SCORE_PERSISTENCE_THRESHOLD:
            if not state.z_score_above_threshold:
                # Just crossed threshold - start tracking
                state.z_score_above_threshold = True
                state.z_score_persistence_start = timestamp
                return False
            else:
                # Already above threshold - check duration
                if timestamp and state.z_score_persistence_start:
                    duration_minutes = (timestamp - state.z_score_persistence_start).total_seconds() / 60
                    return duration_minutes > config.Z_SCORE_PERSISTENCE_MINUTES
                return False
        else:
            # Below threshold - reset tracking
            state.z_score_above_threshold = False
            state.z_score_persistence_start = None
            return False
    
    def _update_price_momentum(self, state: SymbolState, current_price: float, 
                              timestamp: Optional[datetime]) -> float:
        """
        Calculate price momentum using rate of change over multiple timeframes.
        Returns momentum score (positive = upward, negative = downward).
        """
        # price_history and timestamp_history are now always initialized in SymbolState
        
        # Add current price
        state.price_history.append(current_price)
        
        # Keep only last 20 observations (about 1 minute of data)
        if len(state.price_history) > 20:
            state.price_history = state.price_history[-20:]
        
        if len(state.price_history) < 5:
            return 0.0
        
        # Calculate momentum over different timeframes
        short_momentum = (current_price - state.price_history[-3]) / state.price_history[-3] * 100
        medium_momentum = (current_price - state.price_history[-6]) / state.price_history[-6] * 100 if len(state.price_history) >= 6 else 0
        
        # Weight recent momentum more heavily
        momentum = 0.7 * short_momentum + 0.3 * medium_momentum
        return momentum
    
    def _check_price_velocity(self, state: SymbolState, current_price: float) -> bool:
        """
        Detect high price velocity indicating strong directional movement.
        """
        if len(state.price_history) < 10:
            return False
        
        # Calculate price changes over last few ticks
        recent_changes = []
        for i in range(len(state.price_history) - 5, len(state.price_history)):
            if i > 0:
                change = abs(state.price_history[i] - state.price_history[i-1])
                recent_changes.append(change)
        
        if not recent_changes:
            return False
        
        # Check if average recent change is unusually high
        avg_change = sum(recent_changes) / len(recent_changes)
        velocity_threshold = getattr(config, 'VELOCITY_THRESHOLD', 4.0)  # 4 ticks
        
        return avg_change > velocity_threshold
    
    def _check_momentum_divergence(self, state: SymbolState, current_price: float, z_score: float) -> bool:
        """
        Detect momentum divergence: price making new extremes while z-score weakens.
        This can be an early warning of trend exhaustion or continuation.
        """
        if len(state.price_history) < 10:
            return False
        
        state.z_score_history.append(abs(z_score))
        if len(state.z_score_history) > 10:
            state.z_score_history = state.z_score_history[-10:]
        
        # Check for strong momentum with extreme z-score
        recent_prices = state.price_history[-5:]
        recent_z_scores = state.z_score_history[-5:] if len(state.z_score_history) >= 5 else []
        
        if len(recent_z_scores) < 5:
            return False
        
        # Look for price momentum in same direction as extreme z-score
        price_trend = recent_prices[-1] - recent_prices[0]
        z_score_trend = recent_z_scores[-1] - recent_z_scores[0]
        
        # Strong momentum when both price and z-score are moving in same extreme direction
        momentum_threshold = getattr(config, 'MOMENTUM_DIVERGENCE_THRESHOLD', 1.5)
        
        return (abs(price_trend) > momentum_threshold and 
                abs(z_score_trend) > 0.5 and 
                abs(z_score) > 2.5)