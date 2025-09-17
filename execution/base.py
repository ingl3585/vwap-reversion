# execution/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from api.schemas import DecisionMessage

@dataclass
class ExecutionResult:
    """Result of an order execution attempt"""
    success: bool
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    
@dataclass
class ExecutionConfig:
    """Configuration for execution methods"""
    name: str
    enabled: bool = True
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

class BaseExecutor(ABC):
    """Abstract base class for all execution methods"""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self.name = config.name
        
    @abstractmethod
    async def place_order(self, decision: DecisionMessage, symbol: str, **kwargs) -> ExecutionResult:
        """Place an order based on the trading decision"""
        pass
        
    @abstractmethod
    async def cancel_order(self, order_id: str) -> ExecutionResult:
        """Cancel an existing order"""
        pass
        
    @abstractmethod
    async def flatten_position(self, symbol: str) -> ExecutionResult:
        """Flatten all positions for a symbol"""
        pass
        
    @abstractmethod
    async def get_position(self, symbol: str) -> int:
        """Get current position quantity for a symbol"""
        pass
        
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the execution method is properly connected"""
        pass