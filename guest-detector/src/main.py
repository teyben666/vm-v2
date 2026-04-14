"""Guest Detector - Main monitoring loop.

Monitors:
1. Mouse/Keyboard activity (idle detection)
2. Parsec connection status
3. System metrics
4. Executes commands from Host API
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.idle_checker import IdleChecker
from src.parsec_reader import ParsecReader
from src.api_sender import APISender
from src.os_manager import OSManager

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
HOST_LAN_IP = os.getenv("HOST_LAN_IP", "192.168.1.100")
API_PORT = int(os.getenv("API_PORT", 8000))
DETECTOR_ID = os.getenv("DETECTOR_ID")
VM_SECRET_KEY = os.getenv("VM_SECRET_KEY")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", 60))
AFK_THRESHOLD = int(os.getenv("AFK_THRESHOLD_MINUTES", 60))

# Validate config
if not DETECTOR_ID or DETECTOR_ID == "your_detector_id_here":
    logger.error("DETECTOR_ID not configured!")
    sys.exit(1)

if not VM_SECRET_KEY or VM_SECRET_KEY == "your_secret_key_here":
    logger.error("VM_SECRET_KEY not configured!")
    sys.exit(1)


class DetectorLoop:
    """Main background loop for the Guest Detector."""

    def __init__(self):
        self.running = False
        self.idle_checker = IdleChecker()
        self.parsec_reader = ParsecReader()
        self.api_sender = APISender(HOST_LAN_IP, API_PORT, DETECTOR_ID, VM_SECRET_KEY)
        self.os_manager = OSManager()
        
        # State tracking
        self.afk_start_time = None
        self.last_heartbeat = None

    async def run(self):
        """Main detection loop."""
        self.running = True
        logger.info(f"Detector started for {DETECTOR_ID}")
        logger.info(f"Host API: http://{HOST_LAN_IP}:{API_PORT}")

        while self.running:
            try:
                await self._tick()
                await asyncio.sleep(HEARTBEAT_INTERVAL)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.running = False
            except Exception as e:
                logger.error(f"Tick error: {e}", exc_info=True)
                self.stop()  # Clean up resources on error
                await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _tick(self):
        """One heartbeat cycle."""
        # Check Parsec connection FIRST (needed for idle detection)
        parsec_connected = self.parsec_reader.is_connected()
        
        # Check idle status (pass Parsec connection to account for remote input)
        is_idle = self.idle_checker.check_idle(parsec_connected=parsec_connected)
        
        # Update AFK tracking
        current_time = datetime.now()
        if is_idle:
            if self.afk_start_time is None:
                self.afk_start_time = current_time
                logger.info("User went AFK")
        else:
            if self.afk_start_time is not None:
                duration = (current_time - self.afk_start_time).total_seconds() / 60
                logger.info(f"User returned from {duration:.1f}min AFK")
            self.afk_start_time = None

        # Calculate AFK duration (reuse current_time for consistency and efficiency)
        if self.afk_start_time:
            afk_duration = (current_time - self.afk_start_time).total_seconds() / 60
        else:
            afk_duration = 0

        # Log status
        status_msg = (
            f"AFK: {is_idle} ({afk_duration:.1f}min) | "
            f"Parsec: {parsec_connected}"
        )
        logger.debug(status_msg)

        # Check for auto-shutdown (AFK + disconnected for 60min)
        should_auto_shutdown = (
            is_idle and 
            not parsec_connected and 
            afk_duration >= AFK_THRESHOLD
        )

        if should_auto_shutdown:
            logger.warning(
                f"Auto-shutdown triggered: AFK for {afk_duration:.1f}min, Parsec disconnected"
            )
            # Send final heartbeat before shutdown
            try:
                await self.api_sender.send_heartbeat(
                    afk=is_idle,
                    afk_duration_minutes=int(afk_duration),
                    parsec_connected=parsec_connected
                )
            except Exception as e:
                logger.warning(f"Could not send final heartbeat: {e}")
            
            await self.api_sender.send_shutdown_imminent()
            await asyncio.sleep(2)
            self.os_manager.graceful_shutdown(300)  # 5 minute warning
            return

        # Send heartbeat and receive command
        try:
            response = await self.api_sender.send_heartbeat(
                afk=is_idle,
                afk_duration_minutes=int(afk_duration),
                parsec_connected=parsec_connected
            )

            if response and response.get("command"):
                await self._execute_command(response["command"], response)

        except Exception as e:
            logger.error(f"Heartbeat error: {e}")

    async def _execute_command(self, command: str, response: dict):
        """Execute a command received from Host."""
        delay_seconds = response.get("delay_seconds", 0)

        if command == "shutdown":
            logger.info(f"Executing graceful shutdown (delay: {delay_seconds}s)")
            self.os_manager.graceful_shutdown(delay_seconds)
            self.running = False

        elif command == "auto_shutdown_pending":
            logger.warning(f"Auto-shutdown pending in {delay_seconds}s")
            await asyncio.sleep(2)
            self.os_manager.graceful_shutdown(delay_seconds)
            self.running = False

        else:
            logger.warning(f"Unknown command: {command}")

    def stop(self):
        """Stop the detector and clean up resources."""
        self.running = False
        try:
            self.parsec_reader.stop()  # Clean up file watcher
        except Exception as e:
            logger.warning(f"Error stopping Parsec reader: {e}")
        logger.info("Detector stopped")


async def main():
    """Entry point."""
    detector = DetectorLoop()
    try:
        await detector.run()
    finally:
        detector.stop()


if __name__ == "__main__":
    asyncio.run(main())
