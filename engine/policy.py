# engine/policy.py - Improved with industry-standard parameters

import logging
from math import sqrt
import config
from api.schemas import DecisionMessage

logger = logging.getLogger("engine.policy")

class Policy:
    def __init__(
        self,
        z_exit: float = config.DEFAULT_Z_EXIT,
        warmup_observations: int = config.MIN_OBSERVATIONS_FOR_SIGNAL,
        tick_size: float = config.TICK_SIZE,
        min_std_ticks: float = config.MIN_STD_TICKS,
        z_entry_levels: list = None,
        entry_quantities: list = None,
        max_total_position: int = None
    ):
        self.z_exit = z_exit
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
            
        # Reset entry levels if position doesn't match what we expect
        # This handles cases where orders were triggered but didn't execute
        expected_long_position = sum(self.entry_quantities[i] for i, triggered in enumerate(entry_levels_triggered["long"]) if triggered)
        expected_short_position = -sum(self.entry_quantities[i] for i, triggered in enumerate(entry_levels_triggered["short"]) if triggered)
        expected_position = expected_long_position + expected_short_position
        
        if position_qty != expected_position:
            logger.warning(f"Position mismatch: expected={expected_position}, actual={position_qty}. Resetting entry levels.")
            logger.warning(f"Triggered levels - Long: {entry_levels_triggered['long']}, Short: {entry_levels_triggered['short']}")
            # Reset all levels and recalculate based on current position
            entry_levels_triggered["long"] = [False] * len(self.z_entry_levels)
            entry_levels_triggered["short"] = [False] * len(self.z_entry_levels)
            logger.info(f"Entry levels reset. Long: {entry_levels_triggered['long']}, Short: {entry_levels_triggered['short']}")

        # Layered entry logic for long positions (negative z-score, oversold)
        if z_score < 0:
            for i, threshold in enumerate(self.z_entry_levels):
                if z_score < -threshold and not entry_levels_triggered["long"][i]:
                    # Check if we can still add to position
                    if position_qty + self.entry_quantities[i] <= self.max_total_position:
                        logger.info(f"Position check: {position_qty} + {self.entry_quantities[i]} = {position_qty + self.entry_quantities[i]} <= {self.max_total_position}")
                        entry_levels_triggered["long"][i] = True
                        logger.info(f"LONG Level {i+1} triggered: z={z_score:.2f} < -{threshold}, qty={self.entry_quantities[i]}, pos={position_qty}")
                        return DecisionMessage(
                            action="place", 
                            side="buy", 
                            orderType="market",
                            quantity=self.entry_quantities[i]
                        )
                    else:
                        logger.info(f"LONG Level {i+1} blocked by position limit: {position_qty} + {self.entry_quantities[i]} > {self.max_total_position}")
                else:
                    if z_score < -threshold:
                        logger.info(f"LONG Level {i+1} already triggered: z={z_score:.2f} < -{threshold}")
                    else:
                        logger.info(f"LONG Level {i+1} not reached: z={z_score:.2f} >= -{threshold}")

        # Layered entry logic for short positions (positive z-score, overbought)
        if z_score > 0:
            for i, threshold in enumerate(self.z_entry_levels):
                if z_score > threshold and not entry_levels_triggered["short"][i]:
                    # Check if we can still add to position (negative position for shorts)
                    if position_qty - self.entry_quantities[i] >= -self.max_total_position:
                        entry_levels_triggered["short"][i] = True
                        logger.info(f"SHORT Level {i+1} triggered: z={z_score:.2f} > {threshold}, qty={self.entry_quantities[i]}, pos={position_qty}")
                        return DecisionMessage(
                            action="place", 
                            side="sell", 
                            orderType="market",
                            quantity=self.entry_quantities[i]
                        )
                    else:
                        logger.info(f"SHORT Level {i+1} blocked by position limit: {position_qty} - {self.entry_quantities[i]} < -{self.max_total_position}")
                else:
                    if z_score > threshold:
                        logger.info(f"SHORT Level {i+1} already triggered: z={z_score:.2f} > {threshold}")
                    else:
                        logger.info(f"SHORT Level {i+1} not reached: z={z_score:.2f} <= {threshold}")

        return DecisionMessage(action="hold")

