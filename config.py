# config.py

import logging
import sys
from datetime import datetime

# API Configuration
API_TITLE = "ResearchStrategy"
API_HOST = "127.0.0.1"
API_PORT = 8000

# Trading Policy Configuration
DEFAULT_Z_EXIT = 0.5
DEFAULT_MAX_SPREAD_TICKS = 2.0
MIN_OBSERVATIONS_FOR_SIGNAL = 100
TICK_SIZE = 0.25
MIN_STD_TICKS = 2.0

# Layered Entry Configuration
Z_ENTRY_LEVELS = [8.0,  16.5, 24.0]  # Three z-score thresholds for entries
ENTRY_QUANTITIES = [1, 2, 3]         # Corresponding quantities for each level
MAX_TOTAL_POSITION = 6               # Maximum total position across all levels

# Indicator Configuration
EWMA_ALPHA = 0.10
MIN_VOLUME_THRESHOLD = 1e-9
MIN_VARIANCE_THRESHOLD = 4.0

# State Management
MIN_CUMULATIVE_VOLUME = 1e-9
INITIAL_EMA_VARIANCE = 16.0

# Strategy Configuration
ENABLED_STRATEGIES = ["vwap_reversion"]  # List of strategies to run concurrently

# Logging Configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging():
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return logging.getLogger("trading_system")