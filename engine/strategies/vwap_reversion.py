# engine/strategies/vwap_reversion.py

import logging
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
        
        logger.info(
            f"VWAP calculations for {tick.symbolName}: vwap={vwap_price:.4f}, "
            f"deviation={deviation:.4f}, z_score={z_score:.4f}, spread={spread:.4f}, mid={mid_price:.4f}, "
            f"position={tick.positionQty}, entry_levels={state.entry_levels_triggered}"
        )
        
        return self.policy.decide(
            z_score, tick.positionQty, mid_price, spread, 
            state.observationCount, state.emaVariance, tick.tickSize,
            state.entry_levels_triggered
        )