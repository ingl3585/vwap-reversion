# engine/session_manager.py

import logging
from datetime import datetime, time
from typing import Dict, Any, Optional
import config

logger = logging.getLogger("engine.session_manager")

class SessionManager:
    """Manages trading sessions and session-specific parameters"""
    
    def __init__(self):
        self.session_config = config.SESSION_CONFIG
        self.no_trading_periods = config.NO_TRADING_PERIODS
        self.default_session = config.DEFAULT_SESSION
        
    def get_current_session(self, current_time: datetime = None) -> str:
        """Determine current trading session based on Central Time"""
        if current_time is None:
            current_time = datetime.now()
            
        current_time_str = current_time.strftime("%H:%M")
        
        # Check each session
        for session_name, session_config in self.session_config.items():
            if self._is_time_in_session(current_time_str, session_config):
                return session_name
                
        # Return default if no session matches
        logger.warning(f"No session found for time {current_time_str}, using default: {self.default_session}")
        return self.default_session
        
    def _is_time_in_session(self, current_time_str: str, session_config: Dict) -> bool:
        """Check if current time falls within session hours"""
        start_time = session_config["start_time"]
        end_time = session_config["end_time"]
        
        current_time_obj = datetime.strptime(current_time_str, "%H:%M").time()
        start_time_obj = datetime.strptime(start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        
        # Handle overnight sessions (end_time < start_time)
        if end_time_obj < start_time_obj:
            # Overnight session: 17:00 to 06:30 next day
            return current_time_obj >= start_time_obj or current_time_obj <= end_time_obj
        else:
            # Regular session: 06:30 to 15:14
            return start_time_obj <= current_time_obj <= end_time_obj
            
    def get_session_config(self, session_name: str = None, current_time: datetime = None) -> Dict[str, Any]:
        """Get configuration for specified session or current session"""
        if session_name is None:
            session_name = self.get_current_session(current_time)
            
        if session_name not in self.session_config:
            logger.warning(f"Unknown session {session_name}, using default: {self.default_session}")
            session_name = self.default_session
            
        return self.session_config[session_name]
        
    def is_trading_allowed(self, current_time: datetime = None) -> bool:
        """Check if trading is allowed at current time"""
        if current_time is None:
            current_time = datetime.now()
            
        current_time_str = current_time.strftime("%H:%M")
        
        # Check if in no-trading period
        for period in self.no_trading_periods:
            if self._is_time_in_period(current_time_str, period["start"], period["end"]):
                logger.info(f"Trading not allowed - in no-trading period: {period['start']} to {period['end']}")
                return False
                
        return True
        
    def _is_time_in_period(self, current_time_str: str, start_time: str, end_time: str) -> bool:
        """Check if current time falls within a specific period"""
        current_time_obj = datetime.strptime(current_time_str, "%H:%M").time()
        start_time_obj = datetime.strptime(start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        
        # Handle periods that cross midnight
        if end_time_obj < start_time_obj:
            return current_time_obj >= start_time_obj or current_time_obj <= end_time_obj
        else:
            return start_time_obj <= current_time_obj <= end_time_obj
            
    def should_flatten_positions(self, current_time: datetime = None) -> bool:
        """Check if positions should be flattened based on session rules"""
        if current_time is None:
            current_time = datetime.now()
            
        current_session = self.get_current_session(current_time)
        session_config = self.get_session_config(current_session, current_time)
        
        flatten_time = session_config.get("flatten_time")
        if not flatten_time:
            return False
            
        current_time_str = current_time.strftime("%H:%M")
        
        # Check if we've reached or passed the flatten time
        current_time_obj = datetime.strptime(current_time_str, "%H:%M").time()
        flatten_time_obj = datetime.strptime(flatten_time, "%H:%M").time()
        
        return current_time_obj >= flatten_time_obj
        
    def log_session_info(self, current_time: datetime = None):
        """Log current session information"""
        if current_time is None:
            current_time = datetime.now()
            
        current_session = self.get_current_session(current_time)
        session_config = self.get_session_config(current_session, current_time)
        trading_allowed = self.is_trading_allowed(current_time)
        should_flatten = self.should_flatten_positions(current_time)
        
        logger.info(f"Session: {current_session}, Trading: {trading_allowed}, Flatten: {should_flatten}")
        logger.info(f"Z-exit: {session_config['z_exit']}, Entry levels: {session_config['z_entry_levels']}")
        logger.info(f"Max position: {session_config['max_total_position']}, Quantities: {session_config['entry_quantities']}")