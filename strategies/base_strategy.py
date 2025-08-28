# strategies/base_strategy.py

from abc import ABC, abstractmethod
from api.schemas import TickFeature, DecisionMessage
from engine.state import SymbolState

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Defines the interface that all strategies must implement.
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def decide(self, tick: TickFeature, state: SymbolState) -> DecisionMessage:
        """
        Main decision method that all strategies must implement.
        
        Args:
            tick: Market data tick
            state: Symbol-specific state 
            
        Returns:
            DecisionMessage with trading decision
        """
        pass
    
    @abstractmethod
    def reset_session(self, state: SymbolState):
        """Reset strategy-specific state for new session"""
        pass
    
    def get_name(self) -> str:
        """Return strategy name"""
        return self.name