# platforms/topstep_platform.py

import logging
import config
from platforms.base_platform import BasePlatform
from api.schemas import DecisionMessage
from tsxapipy import authenticate, APIClient, OrderPlacer, DataStream

logger = logging.getLogger("topstep_platform")

class TopStepPlatform(BasePlatform):
    """TopStep platform adapter using tsxapi4py"""
    
    def __init__(self):
        self.api_client = None
        self.order_placer = None
        self.data_stream = None
        self.account_id = config.TOPSTEP_ACCOUNT_ID
        self.contract_id = getattr(config, 'TOPSTEP_CONTRACT_ID', 'CON.F.US.NQ.M25')  # Default to NQ
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
            logger.error("tsxapipy not installed. Run: pip install git+https://github.com/mceesincus/tsxapi4py.git")
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
    
    def start_tick_data_stream(self, callback_func):
        """Start real-time tick data streaming"""
        try:
            if not self.api_client:
                raise ValueError("API client not initialized")
            
            def quote_handler(quote_data: dict):
                """Handle incoming tick data and forward to callback"""
                logger.debug(f"TopStep tick data: {quote_data}")
                callback_func(quote_data)
            
            def state_change_handler(state):
                """Handle stream connection state changes"""
                logger.info(f"TopStep stream state: {state}")
            
            self.data_stream = DataStream(
                api_client=self.api_client,
                contract_id_to_subscribe=self.contract_id,
                on_quote_callback=quote_handler,
                on_state_change_callback=state_change_handler
            )
            
            self.data_stream.start()
            logger.info(f"TopStep data stream started for {self.contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to start TopStep data stream: {e}")
            raise
    
    def stop_tick_data_stream(self):
        """Stop the tick data stream"""
        if self.data_stream:
            try:
                self.data_stream.stop()  # Assuming stop method exists
                logger.info("TopStep data stream stopped")
            except Exception as e:
                logger.error(f"Error stopping TopStep data stream: {e}")
    
    def update_stream_token(self):
        """Update the stream token for long-running connections"""
        if self.data_stream and self.api_client:
            try:
                self.data_stream.update_token(self.api_client.current_token)
                logger.debug("TopStep stream token updated")
            except Exception as e:
                logger.error(f"Failed to update TopStep stream token: {e}")

    def get_platform_name(self) -> str:
        return "TopStep"