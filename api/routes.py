# api/routes.py

import logging
from fastapi import APIRouter
from api.schemas import TickFeature, MultiStrategyResponse
from engine.strategy_manager import StrategyManager

logger = logging.getLogger("api.routes")
router = APIRouter()
strategy_manager = StrategyManager()

@router.post("/decide", response_model=MultiStrategyResponse)
def decide(tick: TickFeature) -> MultiStrategyResponse:
    logger.info(f"Received tick: symbol={tick.symbolName}, price={tick.lastPrice}, size={tick.lastSize}, "
                f"bid={tick.bidPrice}, ask={tick.askPrice}, position={tick.positionQty}, session={tick.sessionDate}")
    
    decisions = strategy_manager.process_tick(tick)
    
    for decision in decisions:
        limit_price = getattr(decision, "limitPrice", None)
        logger.info(
            f"Strategy {decision.strategy} decision: action={decision.action}, side={decision.side}, "
            f"qty={decision.quantity}, limit={limit_price}, order_type={decision.orderType}")
    
    return MultiStrategyResponse(decisions=decisions)