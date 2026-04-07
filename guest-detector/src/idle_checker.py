"""Detect user idle status via Windows API."""

import logging
import ctypes
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Windows API structures for GetLastInputInfo
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


class IdleChecker:
    """Monitor keyboard/mouse activity to detect AFK."""

    def __init__(self, idle_threshold_seconds: int = 300):
        """Initialize idle checker.
        
        Args:
            idle_threshold_seconds: Consider user idle after this many seconds
        """
        self.idle_threshold = idle_threshold_seconds
        self.last_activity_time = datetime.now()
        self.last_idle_check_debug = None

    def check_idle(self, parsec_connected: bool = False) -> bool:
        """Check if user is idle based on keyboard/mouse input.
        
        Args:
            parsec_connected: If True, always consider user active (they're using remote desktop)
        
        Returns:
            True if idle, False if active
        """
        # If Parsec is connected, user is actively using remote desktop
        # (their input happens on client side, not detected by VM's GetLastInputInfo)
        if parsec_connected:
            self.last_activity_time = datetime.now()
            return False
        
        try:
            # Get last input time from Windows
            last_input_info = LASTINPUTINFO()
            last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)

            # Call Windows API
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info))

            # Get system uptime
            tick_count = ctypes.windll.kernel32.GetTickCount()

            # Calculate idle time in milliseconds
            idle_time_ms = tick_count - last_input_info.dwTime

            # Convert to seconds
            idle_time_seconds = idle_time_ms / 1000

            # Check if idle
            is_idle = idle_time_seconds >= self.idle_threshold

            if not is_idle:
                self.last_activity_time = datetime.now()

            # Debug logging for troubleshooting
            self.last_idle_check_debug = {
                "idle_time_seconds": idle_time_seconds,
                "threshold_seconds": self.idle_threshold,
                "is_idle": is_idle
            }

            return is_idle

        except Exception as e:
            logger.error(f"Error checking idle status: {e}")
            # Assume active if we can't determine
            return False

    def get_idle_duration(self) -> timedelta:
        """Get how long user has been idle.
        
        Returns:
            Timedelta of idle duration
        """
        if self.check_idle():
            return datetime.now() - self.last_activity_time
        else:
            return timedelta(0)


# For testing in non-Windows environments
if __name__ != "__main__":
    try:
        # Try Windows import
        pass
    except (AttributeError, OSError):
        logger.warning("Running on non-Windows system - idle detection limited")
