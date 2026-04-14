"""Monitor Parsec connection status via log file."""

import logging
import os
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from typing import Optional

logger = logging.getLogger(__name__)


class ParsecLogHandler(FileSystemEventHandler):
    """Watch Parsec log file for connection status changes."""

    def __init__(self):
        self.connected = False
        self.last_update = datetime.now()

    def on_modified(self, event: FileModifiedEvent):
        """Called when Parsec log is modified."""
        if not event.is_directory and "log.txt" in event.src_path:
            self._check_connection()

    def _check_connection(self):
        """Check current Parsec connection status."""
        log_path = os.getenv("PARSEC_LOG_PATH")
        if not log_path or not os.path.exists(log_path):
            self.connected = False
            return

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Check last 500 lines for connection status (more coverage for active logs)
            recent_lines = lines[-500:] if len(lines) > 500 else lines
            
            # Look for indicators of active connection
            # These patterns match actual Parsec log format
            connected_indicators = [
                "connected.",  # Matches "lauzenhao#8144935 connected."
                "peer connected",
                "client connected",
                "connection established",
            ]

            disconnected_indicators = [
                "disconnected.",  # Matches "lauzenhao#8144935 disconnected."
                "peer disconnected",
                "client disconnected",
                "connection closed",
                "disconnected by client",
                "virtual tablet removed due to client disconnect",  # Also a clear disconnect indicator
            ]

            # Check indicators in reverse order (most recent first)
            for line in reversed(recent_lines):
                line_lower = line.lower()
                
                # Prioritize disconnected checks first (more important)
                for indicator in disconnected_indicators:
                    if indicator in line_lower:
                        self.connected = False
                        self.last_update = datetime.now()
                        logger.debug(f"Parsec: Disconnected (matched: '{indicator}')")
                        return

                # Then check connected indicators
                for indicator in connected_indicators:
                    if indicator in line_lower:
                        self.connected = True
                        self.last_update = datetime.now()
                        logger.debug(f"Parsec: Connected (matched: '{indicator}')")
                        return

        except Exception as e:
            logger.error(f"Error reading Parsec log: {e}")
            self.connected = False


class ParsecReader:
    """Monitor Parsec connection status."""

    def __init__(self):
        self.handler = ParsecLogHandler()
        self.observer: Optional[Observer] = None
        self._setup_watcher()

    def _setup_watcher(self):
        """Setup file watcher for Parsec log."""
        log_path = os.getenv("PARSEC_LOG_PATH")

        if not log_path:
            logger.warning("PARSEC_LOG_PATH not configured - assuming always disconnected")
            return

        if not os.path.exists(log_path):
            logger.warning(f"Parsec log not found at {log_path}")
            return

        try:
            log_dir = os.path.dirname(log_path)
            self.observer = Observer()
            self.observer.schedule(self.handler, path=log_dir, recursive=False)
            self.observer.start()
            logger.info(f"Watching Parsec log: {log_path}")

            # Initial check
            self.handler._check_connection()

        except Exception as e:
            logger.error(f"Failed to setup Parsec watcher: {e}")

    def is_connected(self) -> bool:
        """Check if Parsec is currently connected.
        
        Returns:
            True if connected and log is recently updated, False otherwise
        """
        # If log shows disconnected, definitely return False
        if not self.handler.connected:
            return False
        
        # If connected, verify log file is receiving updates
        # (Parsec actively logs data during connection, updates are a sign of active session)
        log_path = os.getenv("PARSEC_LOG_PATH")
        if log_path and os.path.exists(log_path):
            try:
                log_mod_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                time_since_log_update = datetime.now() - log_mod_time
                
                # If log hasn't been updated in 5 minutes, likely disconnected
                if time_since_log_update > timedelta(minutes=5):
                    logger.debug(f"Parsec log stale ({time_since_log_update.total_seconds():.0f}s old) - assuming disconnected")
                    self.handler.connected = False
                    return False
            except Exception as e:
                logger.warning(f"Could not check log file timestamp: {e}")
        
        return self.handler.connected

    def stop(self):
        """Stop watching the log file."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
# Log timestamp verification is now integrated in is_connected()
