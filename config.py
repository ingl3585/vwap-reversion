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
TOPSTEP_CONTRACT_ID = "CON.F.US.NQ.M25"  # Default contract (NQ futures)
TOPSTEP_ENVIRONMENT = "DEMO"  # Options: "DEMO", "LIVE"

# Trading Policy Configuration
DEFAULT_MAX_SPREAD_TICKS = 2.0
MIN_OBSERVATIONS_FOR_SIGNAL = 300
DEFAULT_QUANTITY = 1
MAX_POSITION_SIZE = 2  # Maximum total position size

# Session-Based Z-Score Thresholds
# NY Session (7:30 AM - 4:00 PM CT) - Conservative during high volume
NY_SESSION_Z_ENTRY = 20.0          # Conservative for trend-prone periods
NY_SESSION_Z_EXIT = 0.5
NY_SESSION_Z_SECOND_ENTRY = 40.0   # Very high threshold for scaling

# Overnight Session (4:00 PM - 7:30 AM CT) - Aggressive during low volume  
OVERNIGHT_Z_ENTRY = 6.0            # More responsive for cleaner mean reversion
OVERNIGHT_Z_EXIT = 0.3             # Quicker exits in lower volume
OVERNIGHT_Z_SECOND_ENTRY = 10.0    # Lower threshold for scaling
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
# NY Session in Central Time (CT): 7:30 AM - 4:00 PM CT
NY_SESSION_START_HOUR = 7
NY_SESSION_START_MINUTE = 30
NY_SESSION_END_HOUR = 16
NY_SESSION_END_MINUTE = 0

# Restricted Trading Hours (Central Time) - System will flatten positions during these windows
MORNING_RESTRICTION_START_HOUR = 7
MORNING_RESTRICTION_START_MINUTE = 25
MORNING_RESTRICTION_END_HOUR = 7
MORNING_RESTRICTION_END_MINUTE = 45

AFTERNOON_RESTRICTION_START_HOUR = 15
AFTERNOON_RESTRICTION_START_MINUTE = 15
AFTERNOON_RESTRICTION_END_HOUR = 17
AFTERNOON_RESTRICTION_END_MINUTE = 0

# Enhanced Trend Detection Configuration
MOMENTUM_THRESHOLD = 2.0  # Price momentum threshold (%)
VELOCITY_THRESHOLD = 4.0  # Price velocity threshold (ticks)
MOMENTUM_DIVERGENCE_THRESHOLD = 1.5  # Momentum divergence threshold

# State Management
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