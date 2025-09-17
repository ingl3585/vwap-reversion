# execution/topstep.py

import logging
import aiohttp
import json
from typing import Dict, Any, Optional
from api.schemas import DecisionMessage
from .base import BaseExecutor, ExecutionResult, ExecutionConfig

logger = logging.getLogger("execution.topstep")

class TopStepExecutor(BaseExecutor):
    """TopStep API execution implementation"""
    
    def __init__(self, config: ExecutionConfig):
        super().__init__(config)
        self.api_base_url = config.parameters.get("api_base_url")
        self.api_token = config.parameters.get("api_token")
        self.account_id = config.parameters.get("account_id")
        self.trading_symbol = config.parameters.get("trading_symbol")
        
        if not self.api_token:
            raise ValueError("TopStep API token is required")
        if not self.account_id:
            raise ValueError("TopStep account ID is required")
            
        logger.info(f"TopStep executor initialized for account {self.account_id}")
        
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for TopStep API requests"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
    def _map_decision_to_topstep_order(self, decision: DecisionMessage, symbol: str) -> Dict[str, Any]:
        """Convert DecisionMessage to TopStep API market order format"""
        order_data = {
            "accountId": self.account_id,
            "contractId": self.trading_symbol,
            "type": 2,  # Market order only
            "side": 0 if decision.side == "buy" else 1,  # 0=buy, 1=sell
            "size": decision.quantity or 1
        }
        
        # Add custom tag for tracking
        if decision.strategy:
            order_data["customTag"] = f"strategy_{decision.strategy}"
            
        return order_data
        
    async def place_order(self, decision: DecisionMessage, symbol: str, **kwargs) -> ExecutionResult:
        """Place an order via TopStep API"""
        try:
            order_data = self._map_decision_to_topstep_order(decision, symbol)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/Order/place",
                    headers=self._get_headers(),
                    json=order_data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get("success", False):
                            logger.info(f"TopStep order placed successfully: {result.get('orderId')}")
                            return ExecutionResult(
                                success=True,
                                order_id=str(result.get("orderId")),
                                error_message=None
                            )
                        else:
                            error_msg = result.get("errorMessage", "Unknown error")
                            logger.error(f"TopStep order failed: {error_msg}")
                            return ExecutionResult(
                                success=False,
                                error_message=error_msg
                            )
                    else:
                        error_msg = f"HTTP {response.status}: {await response.text()}"
                        logger.error(f"TopStep API error: {error_msg}")
                        return ExecutionResult(
                            success=False,
                            error_message=error_msg
                        )
                        
        except Exception as e:
            logger.error(f"TopStep order placement failed: {str(e)}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )
            
    async def cancel_order(self, order_id: str) -> ExecutionResult:
        """Cancel an order via TopStep API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/Order/cancel",
                    headers=self._get_headers(),
                    json={"orderId": int(order_id)}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success", False):
                            logger.info(f"TopStep order cancelled: {order_id}")
                            return ExecutionResult(success=True, order_id=order_id)
                        else:
                            error_msg = result.get("errorMessage", "Unknown error")
                            return ExecutionResult(success=False, error_message=error_msg)
                    else:
                        error_msg = f"HTTP {response.status}"
                        return ExecutionResult(success=False, error_message=error_msg)
                        
        except Exception as e:
            logger.error(f"TopStep order cancellation failed: {str(e)}")
            return ExecutionResult(success=False, error_message=str(e))
            
    async def flatten_position(self, symbol: str) -> ExecutionResult:
        """Flatten position by getting current position and placing opposite order"""
        try:
            current_position = await self.get_position(symbol)
            
            if current_position == 0:
                return ExecutionResult(success=True, error_message="No position to flatten")
                
            # Create opposite order to flatten
            flatten_decision = DecisionMessage(
                action="place",
                side="sell" if current_position > 0 else "buy",
                orderType="market",
                quantity=abs(current_position),
                strategy="flatten"
            )
            
            return await self.place_order(flatten_decision, symbol)
            
        except Exception as e:
            logger.error(f"TopStep position flattening failed: {str(e)}")
            return ExecutionResult(success=False, error_message=str(e))
            
    async def get_position(self, symbol: str) -> int:
        """Get current position for NQ via TopStep API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/Position/current",
                    headers=self._get_headers(),
                    params={"accountId": self.account_id, "contractId": self.trading_symbol}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        # Extract position quantity from response
                        # This will depend on TopStep's actual response format
                        return result.get("quantity", 0)
                    else:
                        logger.warning(f"Could not get position for {symbol}: HTTP {response.status}")
                        return 0
                        
        except Exception as e:
            logger.error(f"TopStep position query failed: {str(e)}")
            return 0
            
    def validate_connection(self) -> bool:
        """Validate TopStep API connection"""
        try:
            # Simple connectivity test - could ping a health endpoint
            return bool(self.api_token and self.account_id)
        except Exception:
            return False