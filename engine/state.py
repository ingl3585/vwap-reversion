# engine/state.py

import config
from typing import Dict

class SymbolState:
    __slots__ = (
        "observationCount", "emaDeviation", "emaVariance", "currentSessionDate", "positionQty",
        "adx_values", "high_prices", "low_prices", "z_score_persistence_start", "z_score_above_threshold",
        "scaling_order_sent"
    )
    def __init__(self):
        self.observationCount = 0
        self.emaDeviation = 0.0
        self.emaVariance = config.INITIAL_EMA_VARIANCE
        self.currentSessionDate = None
        self.positionQty = 0
        
        # Trend filter state
        self.adx_values = []  # Rolling ADX values for smoothing
        self.high_prices = []  # For ADX calculation (DM+)
        self.low_prices = []   # For ADX calculation (DM-)
        self.z_score_persistence_start = None  # When z-score first exceeded threshold
        self.z_score_above_threshold = False   # Current z-score status
        
        # Position scaling state
        self.scaling_order_sent = False  # Prevent duplicate scaling orders

    def reset_session(self):
        self.observationCount = 0
        self.emaDeviation = 0.0
        self.emaVariance = config.INITIAL_EMA_VARIANCE
        
        # Reset trend filter state for new session
        self.adx_values.clear()
        self.high_prices.clear()
        self.low_prices.clear()
        self.z_score_persistence_start = None
        self.z_score_above_threshold = False
        self.scaling_order_sent = False
        # Note: positionQty persists across sessions

class StateStore:
    def __init__(self):
        self._symbols: Dict[str, SymbolState] = {}

    def get(self, symbol_name: str) -> SymbolState:
        if symbol_name not in self._symbols:
            self._symbols[symbol_name] = SymbolState()
        return self._symbols[symbol_name]
