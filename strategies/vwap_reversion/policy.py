# strategies/vwap_reversion/policy.py - Improved with industry-standard parameters

from math import sqrt
import logging
import config
from api.schemas import DecisionMessage

class Policy:
    def __init__(
        self,
        z_entry: float = config.DEFAULT_Z_ENTRY,
        z_exit: float = config.DEFAULT_Z_EXIT,
        max_spread_ticks: float = config.DEFAULT_MAX_SPREAD_TICKS,
        default_qty: int = config.DEFAULT_QUANTITY,
        warmup_observations: int = config.MIN_OBSERVATIONS_FOR_SIGNAL,
        tick_size: float = config.TICK_SIZE,
        min_std_ticks: float = config.MIN_STD_TICKS
    ):
        self.z_entry = z_entry
        self.z_exit = z_exit
        self.max_spread_ticks = max_spread_ticks
        self.default_qty = default_qty
        self.warmup_observations = warmup_observations
        self.tick_size = tick_size
        self.min_std_ticks = min_std_ticks
        self.logger = logging.getLogger("policy")

    def decide(self, z_score: float, position_qty: int,
               mid_price: float, spread: float,
               observation_count: int, ema_variance: float, 
               instrument_tick_size: float = None,
               avoid_mean_reversion: bool = False,
               scaling_order_sent: bool = False) -> DecisionMessage:

        # Use instrument-specific tick size if provided, otherwise fall back to default
        effective_tick_size = instrument_tick_size or self.tick_size

        # Warmup guard - need sufficient observations for statistical significance
        if observation_count < self.warmup_observations:
            return DecisionMessage(action="hold")
            
        # Trend filter guard - avoid mean reversion during strong trends
        if avoid_mean_reversion:
            # Still allow exits during trend days, but no new mean reversion entries
            if abs(z_score) < self.z_exit and position_qty != 0:
                return DecisionMessage(action="flatten")
            return DecisionMessage(action="hold")

        # Variance guard - ensure sufficient volatility for meaningful signals
        std_dev = sqrt(max(ema_variance, config.MIN_VARIANCE_THRESHOLD))
        if std_dev < self.min_std_ticks * effective_tick_size:
            return DecisionMessage(action="hold")

        # Spread guard - avoid trading when spreads are too wide
        if spread > self.max_spread_ticks * effective_tick_size:
            return DecisionMessage(action="hold")

        # Exit logic
        if abs(z_score) < self.z_exit and position_qty != 0:
            return DecisionMessage(action="flatten")

        # Entry logic with position scaling
        quantity = self._calculate_scaled_quantity(z_score, position_qty)
        
        # Don't place scaling orders if we already sent one
        abs_z_score = abs(z_score)
        abs_position = abs(position_qty)
        is_scaling_order = abs_position == 1 and abs_z_score >= config.Z_SCORE_SECOND_ENTRY
        
        if is_scaling_order and scaling_order_sent:
            self.logger.debug("Blocking duplicate scaling order")
            return DecisionMessage(action="hold")
        
        # Only place orders if quantity > 0 (scaling logic determines this)
        if quantity > 0:
            
            # Long entry: price significantly below VWAP (oversold)
            if z_score < -self.z_entry:
                return DecisionMessage(
                    action="place", 
                    side="buy", 
                    orderType="market" if is_scaling_order else "limit",
                    quantity=quantity, 
                    limitPrice=None if is_scaling_order else round(mid_price, 2)
                )
            
            # Short entry: price significantly above VWAP (overbought)  
            if z_score > self.z_entry:
                return DecisionMessage(
                    action="place", 
                    side="sell", 
                    orderType="market" if is_scaling_order else "limit",
                    quantity=quantity, 
                    limitPrice=None if is_scaling_order else round(mid_price, 2)
                )

        return DecisionMessage(action="hold")

    def _calculate_scaled_quantity(self, z_score: float, current_position: int) -> int:
        """
        Calculate position size based on z-score extremes and current position.
        
        Logic:
        - z_score 6.0+: 1 contract (if no position)
        - z_score 10.0+: add 1 more contract (if position in same direction < 2)
        """
        abs_z_score = abs(z_score)
        abs_position = abs(current_position)
        
        # Determine intended trade direction
        is_short_signal = z_score > 0  # Positive z-score = short signal
        is_long_signal = z_score < 0   # Negative z-score = long signal
        
        # Check if current position matches intended direction
        position_matches_signal = (
            (is_short_signal and current_position <= 0) or  # Short signal with flat/short position
            (is_long_signal and current_position >= 0)      # Long signal with flat/long position
        )
        
        # First entry at 6+ z-score (no position)
        if abs_z_score >= self.z_entry and current_position == 0:
            return 1
            
        # Second entry at 10+ z-score (if position matches direction and < 2 contracts)
        elif (abs_z_score >= config.Z_SCORE_SECOND_ENTRY and 
              position_matches_signal and abs_position == 1):
            return 1  # Add one more contract in same direction
            
        # No entry if conditions not met
        return 0