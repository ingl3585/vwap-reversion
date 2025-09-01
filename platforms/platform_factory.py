# platforms/platform_factory.py

import logging
import config
from platforms.base_platform import BasePlatform
from platforms.ninjatrader_platform import NinjaTraderPlatform
from platforms.topstep_platform import TopStepPlatform

logger = logging.getLogger("platform_factory")

class PlatformFactory:
    """Factory for creating trading platform adapters"""
    
    @staticmethod
    def create_platform() -> BasePlatform:
        """Create platform adapter based on config"""
        platform_type = config.TRADING_PLATFORM.upper()
        
        if platform_type == "NINJATRADER":
            logger.info("Creating NinjaTrader platform adapter")
            return NinjaTraderPlatform()
        
        elif platform_type == "TOPSTEP":
            logger.info("Creating TopStep platform adapter")
            return TopStepPlatform()
        
        else:
            raise ValueError(f"Unsupported trading platform: {platform_type}")
    
    @staticmethod
    def get_supported_platforms():
        """Get list of supported platform names"""
        return ["NINJATRADER", "TOPSTEP"]