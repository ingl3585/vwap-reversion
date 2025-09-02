# strategies/vwap_reversion/vwap_reversion_strategy.py

import logging
import config
from strategies.base_strategy import BaseStrategy
from api.schemas import TickFeature, DecisionMessage
from engine.state import SymbolState
from strategies.vwap_reversion.indicators import update_ewma_z
from strategies.vwap_reversion.policy import Policy
from strategies.vwap_reversion.trend_filter import TrendFilter

logger = logging.getLogger("vwap_reversion_strategy")

class VWAPReversionStrategy(BaseStrategy):
    """
    VWAP Mean Reversion Strategy with trend filtering and position scaling.
    
    Enters positions when price deviates significantly from VWAP and expects
    mean reversion. Uses ADX and z-score persistence to avoid trading during
    strong trending periods.
    """
    
    def __init__(self):
        super().__init__("VWAP_Reversion")
        self.policy = Policy()
        self.trend_filter = TrendFilter()
        logger.info("VWAPReversionStrategy initialized")
    
    def decide(self, tick: TickFeature, state: SymbolState) -> DecisionMessage:
        """
        Main decision logic for VWAP reversion strategy
        """
        # Calculate VWAP deviation and z-score
        vwap_price = tick.vwap
        deviation = tick.lastPrice - vwap_price
        
        # Increment observation count for warmup logic
        state.observationCount += 1
        
        # Update EWMA indicators
        z_score = update_ewma_z(state, deviation)
        
        # Calculate spread and mid price
        spread = tick.askPrice - tick.bidPrice
        mid_price = 0.5 * (tick.bidPrice + tick.askPrice)
        
        # Check trend filter before making trading decisions
        should_avoid_mean_reversion = self.trend_filter.should_avoid_mean_reversion(
            state, z_score, tick.askPrice, tick.bidPrice, mid_price, tick.timestamp
        )
        
        logger.info(
            f"VWAP Reversion for {tick.symbolName}: vwap={vwap_price:.4f}, "
            f"deviation={deviation:.4f}, z_score={z_score:.4f}, spread={spread:.4f}, "
            f"mid={mid_price:.4f}, trend_filter={should_avoid_mean_reversion}"
        )
        
        # Check if we should reset scaling flag (position changed)
        if abs(tick.positionQty) != 1:  # Position is 0 or 2, reset scaling flag
            state.scaling_order_sent = False
        
        # Delegate decision to policy
        decision = self.policy.decide(
            z_score, tick.positionQty, mid_price, spread,
            state.observationCount, state.emaVariance, tick.tickSize,
            should_avoid_mean_reversion, state.scaling_order_sent
        )
        
        # If we sent a scaling order, mark it to prevent duplicates
        if (decision.action == "place" and abs(tick.positionQty) == 1 and 
            abs(z_score) >= config.Z_SCORE_SECOND_ENTRY):
            state.scaling_order_sent = True
            
        return decision
    
    def reset_session(self, state: SymbolState):
        """Reset strategy-specific state for new session"""
        # The state reset logic is handled in SymbolState.reset_session()
        # This method is here for interface compliance and future extensions
        pass