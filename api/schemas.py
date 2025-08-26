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
