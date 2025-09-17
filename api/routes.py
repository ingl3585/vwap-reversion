# api/routes.py

import logging
import asyncio
from fastapi import APIRouter
from api.schemas import TickFeature, MultiStrategyResponse, ExecutionRequest, ExecutedStrategyResponse, ExecutionResponse
from engine.strategy_manager import StrategyManager
from execution.factory import ExecutionFactory

logger = logging.getLogger("api.routes")
router = APIRouter()
strategy_manager = StrategyManager()

@router.post("/decide", response_model=MultiStrategyResponse)
def decide(tick: TickFeature) -> MultiStrategyResponse:
    """Get trading decisions without execution (for NinjaTrader)"""
    logger.info(f"Received tick: symbol={tick.symbolName}, price={tick.lastPrice}, size={tick.lastSize}, "
                f"bid={tick.bidPrice}, ask={tick.askPrice}, position={tick.positionQty}, session={tick.sessionDate}")
    
    decisions = strategy_manager.process_tick(tick)
    
    # Filter out "hold" decisions - only send actionable decisions to NinjaTrader
    actionable_decisions = [d for d in decisions if d.action != "hold"]
    
    for decision in decisions:
        limit_price = getattr(decision, "limitPrice", None)
        logger.info(
            f"Strategy {decision.strategy} decision: action={decision.action}, side={decision.side}, "
            f"qty={decision.quantity}, limit={limit_price}, order_type={decision.orderType}")
    
    # Only return response if there are actionable decisions
    if actionable_decisions:
        logger.info(f"Sending {len(actionable_decisions)} actionable decisions to NinjaTrader")
        return MultiStrategyResponse(decisions=actionable_decisions)
    else:
        # No actionable decisions - return empty response (NinjaTrader will ignore)
        logger.debug("No actionable decisions - returning empty decisions")
        return MultiStrategyResponse(decisions=[])

@router.post("/execute", response_model=ExecutedStrategyResponse)
async def execute_strategies(request: ExecutionRequest) -> ExecutedStrategyResponse:
    """Get trading decisions and execute them via specified execution method"""
    tick = request.tick
    execution_method = request.execution_method
    
    logger.info(f"Received execution request: symbol={tick.symbolName}, execution_method={execution_method}")
    
    # Get trading decisions
    decisions = strategy_manager.process_tick(tick)
    
    # Create executor
    executor = ExecutionFactory.create_executor(execution_method)
    
    # Execute each decision
    execution_results = []
    
    for decision in decisions:
        logger.info(f"Executing {decision.strategy} decision: {decision.action}")
        
        try:
            if decision.action == "place":
                result = await executor.place_order(decision, tick.symbolName)
            elif decision.action == "flatten":
                result = await executor.flatten_position(tick.symbolName)
            else:  # hold
                result = ExecutionResponse(success=True, error_message="No action needed")
                
            # Convert ExecutionResult to ExecutionResponse
            execution_response = ExecutionResponse(
                success=result.success,
                order_id=result.order_id,
                error_message=result.error_message,
                executed_price=result.executed_price,
                executed_quantity=result.executed_quantity
            )
            
            execution_results.append(execution_response)
            
            if result.success:
                logger.info(f"Successfully executed {decision.strategy}: {result.order_id}")
            else:
                logger.error(f"Failed to execute {decision.strategy}: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Execution error for {decision.strategy}: {str(e)}")
            execution_results.append(ExecutionResponse(
                success=False,
                error_message=str(e)
            ))
    
    return ExecutedStrategyResponse(
        decisions=decisions,
        execution_results=execution_results
    )