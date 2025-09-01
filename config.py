# config.py

import logging
import sys
from datetime import datetime

# API Configuration
API_TITLE = "ResearchStrategy"
API_HOST = "127.0.0.1"
API_PORT = 8000

# Trading Platform Configuration
TRADING_PLATFORM = "NINJATRADER"  # Options: "NINJATRADER", "TOPSTEP"

# TopStep API Configuration
TOPSTEP_API_KEY = ""  # Set your TopStep API key here
TOPSTEP_ACCOUNT_ID = "150KTC-V2-259344-30084132"  # Set your TopStep account ID here
TOPSTEP_ENVIRONMENT = "DEMO"  # Options: "DEMO", "LIVE"

# Trading Policy Configuration
DEFAULT_Z_ENTRY = 6.0  # 3x wider deviation for more conservative entries
DEFAULT_Z_EXIT = 0.5
DEFAULT_MAX_SPREAD_TICKS = 2.0
MIN_OBSERVATIONS_FOR_SIGNAL = 100
DEFAULT_QUANTITY = 1
# Position Scaling Configuration
Z_SCORE_SECOND_ENTRY = 10.0  # Add second position at extreme deviation
MAX_POSITION_SIZE = 2  # Maximum total position size
TICK_SIZE = 0.25
MIN_STD_TICKS = 2.0

# Indicator Configuration
EWMA_ALPHA = 0.10
MIN_VOLUME_THRESHOLD = 1e-9
MIN_VARIANCE_THRESHOLD = 4.0

# Trend Filter Configuration
ADX_TREND_THRESHOLD = 25.0  # ADX > 25 indicates strong trend (avoid mean reversion)
ADX_PERIOD = 14  # Standard ADX calculation period
Z_SCORE_PERSISTENCE_MINUTES = 30  # Minutes above threshold = trend day
Z_SCORE_PERSISTENCE_THRESHOLD = 1.5  # Z-score level for persistence check
# NY Session in Central Time (CT): 8:30 AM - 3:00 PM CT
NY_SESSION_START_HOUR = 8
NY_SESSION_START_MINUTE = 30
NY_SESSION_END_HOUR = 15
NY_SESSION_END_MINUTE = 0

# State Management
MIN_CUMULATIVE_VOLUME = 1e-9
INITIAL_EMA_VARIANCE = 16.0

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