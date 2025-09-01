# engine/engine.py

import logging
import config
from api.schemas import TickFeature, DecisionMessage
from engine.state import StateStore, SymbolState
from strategies.vwap_reversion.vwap_reversion_strategy import VWAPReversionStrategy
from platforms.platform_factory import PlatformFactory

logger = logging.getLogger("engine.engine")

class DecisionEngine:
    def __init__(self):
        self.state_store = StateStore()
        self.strategy = VWAPReversionStrategy()
        self.platform = PlatformFactory.create_platform()
        logger.info(f"DecisionEngine initialized with VWAP Reversion strategy on {self.platform.get_platform_name()}")

    def _maybe_reset_session(self, state: SymbolState, session_date: str, symbol_name: str):
        if state.currentSessionDate and state.currentSessionDate != session_date:
            # Validate session date format and progression
            if not self._is_valid_session_progression(state.currentSessionDate, session_date):
                logger.warning(
                    f"Suspicious session date change for {symbol_name}: "
                    f"{state.currentSessionDate} -> {session_date}"
                )
            
            logger.info(
                f"Session reset for {symbol_name}: {state.currentSessionDate} -> {session_date} "
                f"(had {state.observationCount} observations)"
            )
            state.reset_session()
        state.currentSessionDate = session_date

    def _is_valid_session_progression(self, old_date: str, new_date: str) -> bool:
        try:
            # Basic format check - should be YYYY-MM-DD
            if len(old_date) != 10 or len(new_date) != 10:
                return False
            if old_date[:4].isdigit() and new_date[:4].isdigit():
                old_year = int(old_date[:4])
                new_year = int(new_date[:4])
                # Year shouldn't jump more than 1
                return abs(new_year - old_year) <= 1
            return True
        except (ValueError, IndexError):
            return False

    def _validate_and_update_position(self, state: SymbolState, reported_position: int):
        if state.positionQty != reported_position:
            if state.observationCount > 0:
                logger.warning(
                    f"Position mismatch - Engine: {state.positionQty}, "
                    f"NinjaTrader: {reported_position}. Using NinjaTrader value."
                )
            state.positionQty = reported_position

    def decide(self, tick: TickFeature) -> DecisionMessage:
        state = self.state_store.get(tick.symbolName)
        self._maybe_reset_session(state, tick.sessionDate, tick.symbolName)
        
        # Track position state for validation
        self._validate_and_update_position(state, tick.positionQty)
        
        # Get decision from strategy
        decision = self.strategy.decide(tick, state)
        
        # Execute decision on platform (for TopStep direct execution)
        if config.TRADING_PLATFORM.upper() == "TOPSTEP":
            success = self.platform.send_decision(decision)
            logger.info(f"TopStep order execution: {'SUCCESS' if success else 'FAILED'}")
        
        # Always return decision (for NinjaTrader HTTP response or logging)
        return decision
