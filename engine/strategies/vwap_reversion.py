# engine/strategies/vwap_reversion.py

import logging
from datetime import datetime
from api.schemas import TickFeature, DecisionMessage
from engine.state import SymbolState
from engine.indicators import update_ewma_z
from engine.policy import Policy
from .base import BaseStrategy

logger = logging.getLogger("strategies.vwap_reversion")

class VwapReversionStrategy(BaseStrategy):
    """VWAP mean reversion trading strategy - existing implementation"""
    
    def __init__(self):
        super().__init__("vwap_reversion")
        self.policy = Policy()
        
    def decide(self, tick: TickFeature, state: SymbolState) -> DecisionMessage:
        """Make VWAP reversion trading decision using existing logic"""
        vwap_price = tick.vwap
        deviation = tick.lastPrice - vwap_price
        
        # Increment observation count for warmup logic
        state.observationCount += 1
        z_score = update_ewma_z(state, deviation)
        spread = tick.askPrice - tick.bidPrice
        mid_price = 0.5 * (tick.bidPrice + tick.askPrice)
        
        
        # Sync expected position with actual position from NinjaTrader
        if state.expected_position != tick.positionQty:
            state.expected_position = tick.positionQty
        
        # Parse timestamp and convert UTC to Central Time for session management
        utc_time = datetime.fromisoformat(tick.timestampIso.replace('Z', '+00:00'))
        # Convert UTC to Central Time (UTC-6 standard, UTC-5 daylight)
        # For simplicity, using UTC-5 (Central Daylight Time)
        from datetime import timedelta
        current_time = utc_time - timedelta(hours=5)
        
        decision = self.policy.decide(
            z_score, state.expected_position, mid_price, spread, 
            state.observationCount, state.emaVariance, tick.tickSize,
            state.entry_levels_triggered, current_time
        )
        
        # Update expected position based on decision
        if decision.action == "place":
            if decision.side == "buy":
                state.expected_position += decision.quantity
            elif decision.side == "sell":
                state.expected_position -= decision.quantity
        elif decision.action == "flatten":
            state.expected_position = 0
            
        return decision