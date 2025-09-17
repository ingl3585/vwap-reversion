# engine/strategy_manager.py

import logging
from typing import List, Dict
import config
from api.schemas import TickFeature, DecisionMessage
from engine.state import StateStore
from engine.strategy_factory import StrategyFactory
from engine.strategies.base import BaseStrategy

logger = logging.getLogger("engine.strategy_manager")

class StrategyManager:
    """Manages multiple concurrent trading strategies"""
    
    def __init__(self, enabled_strategies: List[str] = None):
        self.state_store = StateStore()
        enabled_strategies = enabled_strategies or config.ENABLED_STRATEGIES
        
        self.strategies: Dict[str, BaseStrategy] = {}
        for strategy_name in enabled_strategies:
            strategy = StrategyFactory.create_strategy(strategy_name)
            self.strategies[strategy_name] = strategy
            logger.info(f"Loaded strategy: {strategy_name}")
        
        logger.info(f"StrategyManager initialized with {len(self.strategies)} strategies")

    def process_tick(self, tick: TickFeature) -> List[DecisionMessage]:
        """Process tick through all enabled strategies and return independent decisions"""
        decisions = []
        
        for strategy_name, strategy in self.strategies.items():
            try:
                # Each strategy manages its own state completely independently
                strategy_state = strategy.get_state(tick.symbolName)
                
                # Handle session resets per strategy
                self._maybe_reset_strategy_session(strategy_state, tick.sessionDate, tick.symbolName, strategy_name)
                
                # Note: Position tracking is handled within each strategy's decide() method
                # to support expected position tracking for layered entries
                
                decision = strategy.decide(tick, strategy_state)
                
                # Add strategy identifier to the decision
                decision.strategy = strategy_name
                decisions.append(decision)
                
                logger.debug(f"Strategy {strategy_name} decision: {decision.action}")
                
            except Exception as e:
                logger.error(f"Error in strategy {strategy_name}: {e}")
                # Continue with other strategies even if one fails
                continue
        
        return decisions

    def _maybe_reset_strategy_session(self, strategy_state, session_date: str, symbol_name: str, strategy_name: str):
        """Handle session resets per strategy"""
        if strategy_state.currentSessionDate and strategy_state.currentSessionDate != session_date:
            if not self._is_valid_session_progression(strategy_state.currentSessionDate, session_date):
                logger.warning(
                    f"Suspicious session date change for {symbol_name} in {strategy_name}: "
                    f"{strategy_state.currentSessionDate} -> {session_date}"
                )
            
            logger.info(
                f"SESSION RESET TRIGGERED! {strategy_state.currentSessionDate} -> {session_date} "
                f"(entry levels will be cleared)"
            )
            strategy_state.reset_session()
                
        strategy_state.currentSessionDate = session_date

    def _is_valid_session_progression(self, old_date: str, new_date: str) -> bool:
        """Validate session date progression"""
        try:
            if len(old_date) != 10 or len(new_date) != 10:
                return False
            if old_date[:4].isdigit() and new_date[:4].isdigit():
                old_year = int(old_date[:4])
                new_year = int(new_date[:4])
                return abs(new_year - old_year) <= 1
            return True
        except (ValueError, IndexError):
            return False

