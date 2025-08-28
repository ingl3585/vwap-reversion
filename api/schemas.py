# api/schemas.py

from pydantic import BaseModel, computed_field
from datetime import datetime
from typing import Optional

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
    tickSize: float | None = None  # Optional instrument-specific tick size
    
    @computed_field
    @property
    def timestamp(self) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(self.timestampIso.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

class DecisionMessage(BaseModel):
    action: str
    side: str | None = None
    orderType: str | None = None
    quantity: int | None = None
    limitPrice: float | None = None
