# execution/ninjatrader.py

import logging
from api.schemas import DecisionMessage
from .base import BaseExecutor, ExecutionResult, ExecutionConfig

logger = logging.getLogger("execution.ninjatrader")

class NinjaTraderExecutor(BaseExecutor):
    """
    NinjaTrader execution - just logs decisions and returns success.
    NinjaTrader strategy handles the actual order execution.
    """
    
    def __init__(self):
        config = ExecutionConfig(name="ninjatrader")
        super().__init__(config)
        logger.info("NinjaTrader executor initialized")
        
    async def place_order(self, decision: DecisionMessage, symbol: str, **kwargs) -> ExecutionResult:
        """Log the decision - NinjaTrader will handle execution"""
        logger.info(f"NinjaTrader decision for {symbol}: {decision.action}")
        return ExecutionResult(success=True)
        
    async def cancel_order(self, order_id: str) -> ExecutionResult:
        """Not used for NinjaTrader"""
        return ExecutionResult(success=True)
        
    async def flatten_position(self, symbol: str) -> ExecutionResult:
        """Not used for NinjaTrader"""
        return ExecutionResult(success=True)
        
    async def get_position(self, symbol: str) -> int:
        """Not used for NinjaTrader - position comes from tick data"""
        return 0
        
    def validate_connection(self) -> bool:
        """Always true for NinjaTrader"""
        return True