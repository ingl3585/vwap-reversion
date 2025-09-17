# execution/factory.py

import logging
import os
from typing import Dict, Type
import config
from .base import BaseExecutor, ExecutionConfig
from .ninjatrader import NinjaTraderExecutor
from .topstep import TopStepExecutor

logger = logging.getLogger("execution.factory")

class ExecutionFactory:
    """Factory for creating and managing execution methods"""
    
    _executors: Dict[str, Type[BaseExecutor]] = {
        "ninjatrader": NinjaTraderExecutor,
        "topstep": TopStepExecutor,
    }
    
    @classmethod
    def create_executor(cls, execution_method: str = None) -> BaseExecutor:
        """Create an executor instance by method name"""
        execution_method = execution_method or config.DEFAULT_EXECUTION_METHOD
        
        if execution_method not in cls._executors:
            available = list(cls._executors.keys())
            raise ValueError(f"Unknown execution method '{execution_method}'. Available methods: {available}")
        
        executor_class = cls._executors[execution_method]
        
        # Create configuration based on execution method
        if execution_method == "ninjatrader":
            logger.info("Creating NinjaTrader executor")
            return executor_class()
            
        elif execution_method == "topstep":
            # Get TopStep configuration from config and environment variables
            topstep_config = ExecutionConfig(
                name="topstep",
                parameters={
                    "api_base_url": config.TOPSTEP_API_BASE_URL,
                    "api_token": os.getenv("TOPSTEP_API_TOKEN") or config.TOPSTEP_API_TOKEN,
                    "account_id": os.getenv("TOPSTEP_ACCOUNT_ID") or config.TOPSTEP_ACCOUNT_ID,
                    "trading_symbol": config.TOPSTEP_TRADING_SYMBOL
                }
            )
            logger.info("Creating TopStep executor")
            return executor_class(topstep_config)
        
        # This shouldn't happen due to the check above, but just in case
        raise ValueError(f"Unsupported execution method: {execution_method}")
    
    @classmethod
    def register_executor(cls, name: str, executor_class: Type[BaseExecutor]) -> None:
        """Register a new executor class"""
        cls._executors[name] = executor_class
        logger.info(f"Registered executor: {name}")
    
    @classmethod
    def list_executors(cls) -> list[str]:
        """List all available executor names"""
        return list(cls._executors.keys())