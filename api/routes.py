# api/routes.py

import logging
from fastapi import APIRouter
from api.schemas import TickFeature, DecisionMessage
from engine.engine import DecisionEngine

logger = logging.getLogger("api.routes")
router = APIRouter()
engine = DecisionEngine()

@router.post("/decide", response_model=DecisionMessage)
def decide(tick: TickFeature) -> DecisionMessage:
    logger.info(f"Received tick: symbol={tick.symbolName}, price={tick.lastPrice}, size={tick.lastSize}, "
                f"bid={tick.bidPrice}, ask={tick.askPrice}, position={tick.positionQty}, session={tick.sessionDate}")
    
    decision = engine.decide(tick)
    
    limit_price = getattr(decision, "limitPrice", None)
    logger.info(
        f"Decision: action={decision.action}, side={decision.side}, qty={decision.quantity}, "
        f"limit={limit_price}, order_type={decision.orderType}")
    
    return decision