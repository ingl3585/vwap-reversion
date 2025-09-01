# platforms/base_platform.py

from abc import ABC, abstractmethod
from api.schemas import DecisionMessage

class BasePlatform(ABC):
    """Base class for trading platform adapters"""
    
    @abstractmethod
    def send_decision(self, decision: DecisionMessage) -> bool:
        """Send trading decision to platform. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform identifier"""
        pass