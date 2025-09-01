# platforms/topstep_platform.py

import logging
import config
from platforms.base_platform import BasePlatform
from api.schemas import DecisionMessage
from tsxapi4py.auth import authenticate
from tsxapi4py.api_client import APIClient
from tsxapi4py.order_placer import OrderPlacer

logger = logging.getLogger("topstep_platform")

class TopStepPlatform(BasePlatform):
    """TopStep platform adapter using tsxapi4py"""
    
    def __init__(self):
        self.api_client = None
        self.order_placer = None
        self.account_id = config.TOPSTEP_ACCOUNT_ID
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize TopStep API client and order placer"""
        try:
            # Authenticate and create API client
            if not config.TOPSTEP_API_KEY:
                raise ValueError("TOPSTEP_API_KEY not configured")
            
            token_str, acquired_at_dt = authenticate()
            self.api_client = APIClient(initial_token=token_str)
            
            # Initialize order placer
            if not self.account_id:
                raise ValueError("TOPSTEP_ACCOUNT_ID not configured")
            
            self.order_placer = OrderPlacer(
                api_client=self.api_client, 
                account_id=self.account_id
            )
            
            logger.info(f"TopStep API initialized for account {self.account_id}")
            
        except ImportError:
            logger.error("tsxapi4py not installed. Run: pip install git+https://github.com/mceesincus/tsxapi4py.git")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize TopStep API: {e}")
            raise
    
    def send_decision(self, decision: DecisionMessage) -> bool:
        """Send trading decision to TopStep via API"""
        try:
            if decision.action == "hold":
                return True
            
            elif decision.action == "flatten":
                # Close all positions
                logger.info("TopStep: Flattening position")
                # Note: Implementation would depend on tsxapi4py's position closing methods
                # This is a placeholder for the actual API call
                return True
            
            elif decision.action == "place":
                # Place new order
                side = decision.side.upper()
                quantity = decision.quantity
                
                if decision.orderType == "market":
                    logger.info(f"TopStep: Placing MARKET {side} order for {quantity} contracts")
                    order_id = self.order_placer.place_market_order(
                        side=side, 
                        size=quantity
                    )
                else:  # limit order
                    limit_price = decision.limitPrice
                    logger.info(f"TopStep: Placing LIMIT {side} order for {quantity} contracts at {limit_price}")
                    order_id = self.order_placer.place_limit_order(
                        side=side, 
                        size=quantity, 
                        price=limit_price
                    )
                
                logger.info(f"TopStep order placed: {order_id}")
                return True
                
        except Exception as e:
            logger.error(f"TopStep order failed: {e}")
            return False
        
        return False
    
    def get_platform_name(self) -> str:
        return "TopStep"