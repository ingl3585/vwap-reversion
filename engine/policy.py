# engine/policy.py - Improved with industry-standard parameters

import logging
from math import sqrt
from datetime import datetime
import config
from api.schemas import DecisionMessage
from engine.session_manager import SessionManager

logger = logging.getLogger("engine.policy")

class Policy:
    def __init__(
        self,
        warmup_observations: int = config.MIN_OBSERVATIONS_FOR_SIGNAL,
        tick_size: float = config.TICK_SIZE,
        min_std_ticks: float = config.MIN_STD_TICKS
    ):
        self.warmup_observations = warmup_observations
        self.tick_size = tick_size
        self.min_std_ticks = min_std_ticks
        self.session_manager = SessionManager()

    def decide(self, z_score: float, position_qty: int,
               mid_price: float, spread: float,
               observation_count: int, ema_variance: float, 
               instrument_tick_size: float = None, 
               entry_levels_triggered: dict = None,
               current_time: datetime = None) -> DecisionMessage:

        # Get session-specific parameters
        session_config = self.session_manager.get_session_config(current_time=current_time)
        z_exit = session_config["z_exit"]
        z_entry_levels = session_config["z_entry_levels"]
        entry_quantities = session_config["entry_quantities"]
        max_total_position = session_config["max_total_position"]
        

        # Check if trading is allowed
        if not self.session_manager.is_trading_allowed(current_time):
            return DecisionMessage(action="hold")

        # Check if positions should be flattened (e.g., at 3:14pm)
        if self.session_manager.should_flatten_positions(current_time) and position_qty != 0:
            logger.info("Session flatten time reached - flattening all positions")
            return DecisionMessage(action="flatten")

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
            entry_levels_triggered = {"long": [False] * len(z_entry_levels), 
                                    "short": [False] * len(z_entry_levels)}
            logger.info(f"ENTRY LEVELS INITIALIZED: {entry_levels_triggered}")
        else:
            logger.info(f"ENTRY LEVELS STATE: {entry_levels_triggered}")
        # Note: Removed automatic resizing to prevent resetting triggered levels
        # If session changes during trading, levels will be reset on next session reset

        # Exit logic - if position moves back toward VWAP, exit and reset all levels
        if abs(z_score) < z_exit and position_qty != 0:
            # Reset all entry levels when exiting
            entry_levels_triggered["long"] = [False] * len(z_entry_levels)
            entry_levels_triggered["short"] = [False] * len(z_entry_levels)
            return DecisionMessage(action="flatten")

        # Check if we've exceeded max position
        if abs(position_qty) >= max_total_position:
            return DecisionMessage(action="hold")
            
        # Note: Removed position mismatch reset logic as it was causing
        # entry levels to reset incorrectly and trigger multiple orders

        # Layered entry logic for long positions (negative z-score, oversold)
        if z_score < 0:
            for i, threshold in enumerate(z_entry_levels):
                if z_score < -threshold and not entry_levels_triggered["long"][i]:
                    # Check if we can still add to position
                    if position_qty + entry_quantities[i] <= max_total_position:
                        logger.info(f"Position check: {position_qty} + {entry_quantities[i]} = {position_qty + entry_quantities[i]} <= {max_total_position}")
                        entry_levels_triggered["long"][i] = True
                        logger.info(f"LONG Level {i+1} triggered: z={z_score:.2f} < -{threshold}, qty={entry_quantities[i]}, pos={position_qty}")
                        return DecisionMessage(
                            action="place", 
                            side="buy", 
                            orderType="market",
                            quantity=entry_quantities[i]
                        )
                    else:
                        logger.info(f"LONG Level {i+1} blocked by position limit: {position_qty} + {entry_quantities[i]} > {max_total_position}")
                else:
                    if z_score < -threshold:
                        logger.info(f"LONG Level {i+1} already triggered: z={z_score:.2f} < -{threshold}")

        # Layered entry logic for short positions (positive z-score, overbought)
        if z_score > 0:
            for i, threshold in enumerate(z_entry_levels):
                if z_score > threshold and not entry_levels_triggered["short"][i]:
                    # Check if we can still add to position (negative position for shorts)
                    if position_qty - entry_quantities[i] >= -max_total_position:
                        entry_levels_triggered["short"][i] = True
                        logger.info(f"SHORT Level {i+1} triggered: z={z_score:.2f} > {threshold}, qty={entry_quantities[i]}, pos={position_qty}")
                        return DecisionMessage(
                            action="place", 
                            side="sell", 
                            orderType="market",
                            quantity=entry_quantities[i]
                        )
                    else:
                        logger.info(f"SHORT Level {i+1} blocked by position limit: {position_qty} - {entry_quantities[i]} < -{max_total_position}")
                else:
                    if z_score > threshold:
                        logger.info(f"SHORT Level {i+1} already triggered: z={z_score:.2f} > {threshold}")

        return DecisionMessage(action="hold")

