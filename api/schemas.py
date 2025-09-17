# api/schemas.py

from pydantic import BaseModel

class TickFeature(BaseModel):
    symbolName: str
    timestampIso: str
    lastPrice: float
    lastSize: int
    bidPrice: float
    askPrice: float
    positionQty: int
    sessionDate: str
    vwap: float
    tickSize: float | None = None

class DecisionMessage(BaseModel):
    action: str
    side: str | None = None
    orderType: str | None = None
    quantity: int | None = None
    limitPrice: float | None = None
    strategy: str | None = None

class ExecutionRequest(BaseModel):
    tick: TickFeature
    execution_method: str | None = None  # Optional override for execution method

class ExecutionResponse(BaseModel):
    success: bool
    order_id: str | None = None
    error_message: str | None = None
    executed_price: float | None = None
    executed_quantity: int | None = None

class MultiStrategyResponse(BaseModel):
    decisions: list[DecisionMessage]
    
class ExecutedStrategyResponse(BaseModel):
    decisions: list[DecisionMessage]
    execution_results: list[ExecutionResponse]
