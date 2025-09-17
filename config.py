# config.py

import logging
import sys
import os
from datetime import datetime

# API Configuration
API_TITLE = "ResearchStrategy"
API_HOST = "127.0.0.1"
API_PORT = 8000

# Trading Policy Configuration
MIN_OBSERVATIONS_FOR_SIGNAL = 100
TICK_SIZE = 0.25
MIN_STD_TICKS = 2.0

# Session Configuration (Central Time)
SESSION_CONFIG = {
    "ny_session": {
        "start_time": "07:20",  # 7:20 AM CT
        "end_time": "15:15",    # 3:15 PM CT
        "flatten_time": "15:14", # Flatten all positions at 3:14 PM
        "z_exit": 2.5,
        "z_entry_levels": [20.0, 40.5, 75.0],
        "entry_quantities": [1, 1, 1],
        "max_total_position": 3
    },
    "overnight_session": {
        "start_time": "17:00",  # 5:00 PM CT
        "end_time": "07:20",    # 7:20 AM CT (next day)
        "flatten_time": None,   # No forced flatten for overnight
        "z_exit": 0.5,          # Tighter exit for overnight
        "z_entry_levels": [8.0, 16.0, 20.0],  # Higher thresholds for overnight
        "entry_quantities": [1, 1, 1],        # Smaller position sizes
        "max_total_position": 3               # Lower max position
    }
}

# Default session fallback
DEFAULT_SESSION = "ny_session"

# No trading periods (Central Time)
NO_TRADING_PERIODS = [
    {"start": "15:14", "end": "16:00"},  # Post-close, no new positions
    {"start": "16:00", "end": "17:00"}   # Maintenance window
]

# Indicator Configuration
EWMA_ALPHA = 0.10
MIN_VOLUME_THRESHOLD = 1e-9
MIN_VARIANCE_THRESHOLD = 4.0
BIAS_CORRECTION_PERIOD = 20  # Number of observations for EWMA bias correction

# State Management
MIN_CUMULATIVE_VOLUME = 1e-9
INITIAL_EMA_VARIANCE = 16.0

# Strategy Configuration
ENABLED_STRATEGIES = ["vwap_reversion"]  # List of strategies to run concurrently

# Execution Configuration
DEFAULT_EXECUTION_METHOD = "ninjatrader"  # Options: "ninjatrader", "topstep"

# TopStep API Configuration (only used when execution method is "topstep")
TOPSTEP_API_BASE_URL = "https://gateway-api.s2f.projectx.com"
# Use code topstep for 50% off next time
# 
TOPSTEP_API_TOKEN = os.getenv("TOPSTEP_API_TOKEN")
TOPSTEP_ACCOUNT_ID = os.getenv("TOPSTEP_ACCOUNT_ID")
TOPSTEP_TRADING_SYMBOL = "NQ"  # The symbol to trade on TopStep

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