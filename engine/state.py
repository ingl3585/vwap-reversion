# engine/state.py

import config
from typing import Dict

class SymbolState:
    __slots__ = (
        "observationCount", "emaDeviation", "emaVariance", "currentSessionDate", "positionQty",
        "entry_levels_triggered"
    )
    def __init__(self):
        self.observationCount = 0
        self.emaDeviation = 0.0
        self.emaVariance = config.INITIAL_EMA_VARIANCE
        self.currentSessionDate = None
        self.positionQty = 0
        self.entry_levels_triggered = {"long": [False] * len(config.Z_ENTRY_LEVELS), 
                                     "short": [False] * len(config.Z_ENTRY_LEVELS)}

    def reset_session(self):
        self.observationCount = 0
        self.emaDeviation = 0.0
        self.emaVariance = config.INITIAL_EMA_VARIANCE
        self.entry_levels_triggered = {"long": [False] * len(config.Z_ENTRY_LEVELS), 
                                     "short": [False] * len(config.Z_ENTRY_LEVELS)}

class StateStore:
    def __init__(self):
        self._symbols: Dict[str, SymbolState] = {}

    def get(self, symbol_name: str) -> SymbolState:
        if symbol_name not in self._symbols:
            self._symbols[symbol_name] = SymbolState()
        return self._symbols[symbol_name]
