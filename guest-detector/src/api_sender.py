"""Send HTTP heartbeats to Host API."""

import logging
import httpx
import json
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class APISender:
    """Send heartbeats and receive commands from Host."""

    def __init__(
        self,
        host_ip: str,
        api_port: int,
        detector_id: str,
        secret_key: str,
        timeout: int = 10
    ):
        self.host_ip = host_ip
        self.api_port = api_port
        self.detector_id = detector_id
        self.secret_key = secret_key
        self.timeout = timeout
        self.base_url = f"http://{host_ip}:{api_port}/api"

    async def send_heartbeat(
        self,
        afk: bool,
        afk_duration_minutes: int,
        parsec_connected: bool,
        memory_usage_percent: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None
    ) -> Optional[Dict]:
        """Send heartbeat to Host and receive command.
        
        Args:
            afk: Whether user is idle
            afk_duration_minutes: How long user has been idle
            parsec_connected: Whether Parsec is connected
            memory_usage_percent: Optional memory usage
            cpu_usage_percent: Optional CPU usage
            
        Returns:
            Response dict with possible command, or None if error
        """
        headers = {
            "X-Detector-ID": self.detector_id,
            "X-VM-Secret": self.secret_key,
            "Content-Type": "application/json"
        }

        payload = {
            "afk": afk,
            "afk_duration_minutes": afk_duration_minutes,
            "parsec_connected": parsec_connected,
        }

        if memory_usage_percent is not None:
            payload["memory_usage_percent"] = memory_usage_percent

        if cpu_usage_percent is not None:
            payload["cpu_usage_percent"] = cpu_usage_percent

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/heartbeat",
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.debug(f"Heartbeat acknowledged")
                    return response.json()

                elif response.status_code == 401:
                    logger.error("Authentication failed - Invalid secret key!")
                    return None

                elif response.status_code == 403:
                    logger.error("Max auth attempts exceeded - System lockout!")
                    return None

                else:
                    logger.warning(f"Heartbeat failed: HTTP {response.status_code}")
                    return None

        except httpx.ConnectError:
            logger.error(f"Cannot connect to Host at {self.base_url}")
            return None

        except httpx.TimeoutException:
            logger.warning(f"Heartbeat timeout after {self.timeout}s")
            return None

        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return None

    async def send_alert(
        self,
        alert_type: str,
        message: str
    ) -> bool:
        """Send special alert to Host.
        
        Args:
            alert_type: Type of alert (e.g., "shutdown_imminent")
            message: Alert message
            
        Returns:
            True if sent successfully
        """
        headers = {
            "X-Detector-ID": self.detector_id,
            "X-VM-Secret": self.secret_key,
            "Content-Type": "application/json"
        }

        payload = {
            "type": alert_type,
            "message": message
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/alert",
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.info(f"Alert sent: {alert_type}")
                    return True
                else:
                    logger.warning(f"Alert failed: HTTP {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Alert send error: {e}")
            return False

    async def send_shutdown_imminent(self) -> bool:
        """Notify Host that VM will shutdown soon."""
        return await self.send_alert(
            "shutdown_imminent",
            "VM will auto-shutdown due to 60min idle + disconnected"
        )
