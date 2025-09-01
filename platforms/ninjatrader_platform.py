# platforms/ninjatrader_platform.py

import logging
from platforms.base_platform import BasePlatform
from api.schemas import DecisionMessage

logger = logging.getLogger("ninjatrader_platform")

class NinjaTraderPlatform(BasePlatform):
    """NinjaTrader platform adapter - currently HTTP-based via C# strategy"""
    
    def send_decision(self, decision: DecisionMessage) -> bool:
        """
        For NinjaTrader, decisions are sent back as HTTP responses.
        The C# ResearchStrategy.cs handles order execution.
        """
        logger.debug(f"NinjaTrader decision: {decision.action}")
        return True  # Always successful for HTTP response model
    
    def get_platform_name(self) -> str:
        return "NinjaTrader"