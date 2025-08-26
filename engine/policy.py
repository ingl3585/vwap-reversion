# engine/policy.py - Improved with industry-standard parameters

from math import sqrt
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
        min_std_ticks: float = config.MIN_STD_TICKS,
        enable_adaptive_sizing: bool = False
    ):
        self.z_entry = z_entry
        self.z_exit = z_exit
        self.max_spread_ticks = max_spread_ticks
        self.default_qty = default_qty
        self.warmup_observations = warmup_observations
        self.tick_size = tick_size
        self.min_std_ticks = min_std_ticks
        self.enable_adaptive_sizing = enable_adaptive_sizing

    def decide(self, z_score: float, position_qty: int,
               mid_price: float, spread: float,
               observation_count: int, ema_variance: float, 
               instrument_tick_size: float = None) -> DecisionMessage:

        # Use instrument-specific tick size if provided, otherwise fall back to default
        effective_tick_size = instrument_tick_size or self.tick_size

        # Warmup guard - need sufficient observations for statistical significance
        if observation_count < self.warmup_observations:
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

        # Entry logic
        quantity = self._calculate_quantity(z_score) if self.enable_adaptive_sizing else self.default_qty
        
        # Long entry: price significantly below VWAP (oversold)
        if z_score < -self.z_entry and position_qty <= 0:
            return DecisionMessage(
                action="place", 
                side="buy", 
                orderType="limit",
                quantity=quantity, 
                limitPrice=round(mid_price, 2)
            )
        
        # Short entry: price significantly above VWAP (overbought)  
        if z_score > self.z_entry and position_qty >= 0:
            return DecisionMessage(
                action="place", 
                side="sell", 
                orderType="limit",
                quantity=quantity, 
                limitPrice=round(mid_price / effective_tick_size) * effective_tick_size
            )

        return DecisionMessage(action="hold")

    def _calculate_quantity(self, z_score: float) -> int:
        if not self.enable_adaptive_sizing:
            return self.default_qty
            
        # Scale quantity based on how extreme the z-score is
        # z_score of 2.0 = 1x, z_score of 3.0 = 1.5x, z_score of 4.0 = 2x
        confidence_multiplier = min(abs(z_score) / self.z_entry, 2.0)  # Cap at 2x
        adaptive_qty = max(1, int(self.default_qty * confidence_multiplier))
        
        return adaptive_qty