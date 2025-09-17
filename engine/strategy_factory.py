# engine/strategy_factory.py

import logging
from typing import Dict, Type
from engine.strategies.base import BaseStrategy
from engine.strategies.vwap_reversion import VwapReversionStrategy

logger = logging.getLogger("engine.strategy_factory")

class StrategyFactory:
    """Factory for creating and managing trading strategies"""
    
    _strategies: Dict[str, Type[BaseStrategy]] = {
        "vwap_reversion": VwapReversionStrategy,
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str) -> BaseStrategy:
        """Create a strategy instance by name"""
        if strategy_name not in cls._strategies:
            available = list(cls._strategies.keys())
            raise ValueError(f"Unknown strategy '{strategy_name}'. Available strategies: {available}")
        
        strategy_class = cls._strategies[strategy_name]
        logger.info(f"Creating strategy: {strategy_name}")
        return strategy_class()
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """Register a new strategy class"""
        cls._strategies[name] = strategy_class
        logger.info(f"Registered strategy: {name}")
    
    @classmethod
    def list_strategies(cls) -> list[str]:
        """List all available strategy names"""
        return list(cls._strategies.keys())