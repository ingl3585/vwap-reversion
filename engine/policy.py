# engine/policy.py - Improved with industry-standard parameters

from math import sqrt
import config
from api.schemas import DecisionMessage

class Policy:
    def __init__(
        self,
        z_exit: float = config.DEFAULT_Z_EXIT,
        max_spread_ticks: float = config.DEFAULT_MAX_SPREAD_TICKS,
        warmup_observations: int = config.MIN_OBSERVATIONS_FOR_SIGNAL,
        tick_size: float = config.TICK_SIZE,
        min_std_ticks: float = config.MIN_STD_TICKS,
        z_entry_levels: list = None,
        entry_quantities: list = None,
        max_total_position: int = None
    ):
        self.z_exit = z_exit
        self.max_spread_ticks = max_spread_ticks
        self.warmup_observations = warmup_observations
        self.tick_size = tick_size
        self.min_std_ticks = min_std_ticks
        self.z_entry_levels = z_entry_levels or config.Z_ENTRY_LEVELS
        self.entry_quantities = entry_quantities or config.ENTRY_QUANTITIES
        self.max_total_position = max_total_position or config.MAX_TOTAL_POSITION

    def decide(self, z_score: float, position_qty: int,
               mid_price: float, spread: float,
               observation_count: int, ema_variance: float, 
               instrument_tick_size: float = None, 
               entry_levels_triggered: dict = None) -> DecisionMessage:

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

        # Initialize entry levels tracking if not provided
        if entry_levels_triggered is None:
            entry_levels_triggered = {"long": [False] * len(self.z_entry_levels), 
                                    "short": [False] * len(self.z_entry_levels)}

        # Exit logic - if position moves back toward VWAP, exit and reset all levels
        if abs(z_score) < self.z_exit and position_qty != 0:
            # Reset all entry levels when exiting
            entry_levels_triggered["long"] = [False] * len(self.z_entry_levels)
            entry_levels_triggered["short"] = [False] * len(self.z_entry_levels)
            return DecisionMessage(action="flatten")

        # Check if we've exceeded max position
        if abs(position_qty) >= self.max_total_position:
            return DecisionMessage(action="hold")

        # Layered entry logic for long positions (negative z-score, oversold)
        if z_score < 0:
            for i, threshold in enumerate(self.z_entry_levels):
                if z_score < -threshold and not entry_levels_triggered["long"][i]:
                    # Check if we can still add to position
                    if position_qty + self.entry_quantities[i] <= self.max_total_position:
                        entry_levels_triggered["long"][i] = True
                        return DecisionMessage(
                            action="place", 
                            side="buy", 
                            orderType="limit",
                            quantity=self.entry_quantities[i], 
                            limitPrice=round(mid_price, 2)
                        )

        # Layered entry logic for short positions (positive z-score, overbought)
        if z_score > 0:
            for i, threshold in enumerate(self.z_entry_levels):
                if z_score > threshold and not entry_levels_triggered["short"][i]:
                    # Check if we can still add to position (negative position for shorts)
                    if position_qty - self.entry_quantities[i] >= -self.max_total_position:
                        entry_levels_triggered["short"][i] = True
                        return DecisionMessage(
                            action="place", 
                            side="sell", 
                            orderType="limit",
                            quantity=self.entry_quantities[i], 
                            limitPrice=round(mid_price / effective_tick_size) * effective_tick_size
                        )

        return DecisionMessage(action="hold")

