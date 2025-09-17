# engine/state.py

import config
from typing import Dict

class SymbolState:
    __slots__ = (
        "observationCount", "emaDeviation", "emaVariance", "currentSessionDate", "positionQty",
        "entry_levels_triggered", "expected_position"
    )
    def __init__(self):
        self.observationCount = 0
        self.emaDeviation = 0.0
        self.emaVariance = config.INITIAL_EMA_VARIANCE
        self.currentSessionDate = None
        self.positionQty = 0
        self.expected_position = 0  # Track expected position based on orders placed
        # Initialize with default session (will be resized as needed)
        default_session_config = config.SESSION_CONFIG[config.DEFAULT_SESSION]
        self.entry_levels_triggered = {"long": [False] * len(default_session_config["z_entry_levels"]), 
                                     "short": [False] * len(default_session_config["z_entry_levels"])}

    def reset_session(self):
        self.observationCount = 0
        self.emaDeviation = 0.0
        self.emaVariance = config.INITIAL_EMA_VARIANCE
        self.expected_position = 0
        # Reset with default session (will be resized as needed)
        default_session_config = config.SESSION_CONFIG[config.DEFAULT_SESSION]
        self.entry_levels_triggered = {"long": [False] * len(default_session_config["z_entry_levels"]), 
                                     "short": [False] * len(default_session_config["z_entry_levels"])}

class StateStore:
    def __init__(self):
        self._symbols: Dict[str, SymbolState] = {}

    def get(self, symbol_name: str) -> SymbolState:
        if symbol_name not in self._symbols:
            self._symbols[symbol_name] = SymbolState()
        return self._symbols[symbol_name]
