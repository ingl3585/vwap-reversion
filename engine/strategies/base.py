# engine/strategies/base.py

from abc import ABC, abstractmethod
from typing import Dict
from api.schemas import TickFeature, DecisionMessage
from engine.state import SymbolState

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self._state_store: Dict[str, SymbolState] = {}

    @abstractmethod
    def decide(self, tick: TickFeature, state: SymbolState) -> DecisionMessage:
        """Make trading decision based on tick data and current state"""
        pass

    def get_state(self, symbol: str) -> SymbolState:
        """Get or create state for a symbol"""
        if symbol not in self._state_store:
            self._state_store[symbol] = SymbolState()
        return self._state_store[symbol]