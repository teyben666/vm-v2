"""Execute OS-level commands (shutdown, etc.)."""

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class OSManager:
    """Manage OS-level operations like shutdown."""

    @staticmethod
    def graceful_shutdown(delay_seconds: int = 0) -> bool:
        """Execute graceful Windows shutdown.
        
        Args:
            delay_seconds: Delay before shutdown in seconds
            
        Returns:
            True if command executed successfully
        """
        try:
            if delay_seconds > 0:
                # shutdown /s = shutdown, /t delay in seconds, /c comment, /f = force close apps
                cmd = f'shutdown /s /t {delay_seconds} /c "VM Manager: Graceful shutdown" /f'
            else:
                # Immediate shutdown
                cmd = 'shutdown /s /t 0 /c "VM Manager: Immediate shutdown" /f'

            logger.warning(f"Executing: {cmd}")

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"Shutdown initiated (delay: {delay_seconds}s)")
                return True
            else:
                stderr_msg = result.stderr if result.stderr else result.stdout
                logger.error(f"Shutdown failed: {stderr_msg}")
                
                # Try alternative method - use taskkill to force immediate shutdown if graceful fails
                if delay_seconds == 0:
                    logger.warning("Attempting alternative shutdown method...")
                    alt_cmd = "wmic os where name='%computername%' call shutdown /addtional:0"
                    result_alt = subprocess.run(alt_cmd, shell=True, capture_output=True, timeout=5)
                    if result_alt.returncode == 0:
                        logger.info("Alternative shutdown method succeeded")
                        return True
                
                return False

        except subprocess.TimeoutExpired:
            logger.error("Shutdown command timeout")
            return False
        except Exception as e:
            logger.error(f"Exception during shutdown: {str(e)}")
            return False

    @staticmethod
    def cancel_shutdown() -> bool:
        """Cancel pending shutdown.
        
        Returns:
            True if cancelled successfully
        """
        try:
            cmd = "shutdown /a"
            logger.info("Cancelling pending shutdown")

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("Shutdown cancelled")
                return True
            else:
                logger.warning(f"Could not cancel shutdown: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling shutdown: {e}")
            return False

    @staticmethod
    def get_system_metrics() -> dict:
        """Get basic system metrics.
        
        Returns:
            Dict with memory and CPU usage percentages
        """
        try:
            # This is a simplified version - could use psutil for production
            import subprocess

            # Get memory info
            mem_result = subprocess.run(
                "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value",
                capture_output=True,
                text=True,
                timeout=5
            )

            metrics = {"memory_percent": 0, "cpu_percent": 0}

            # Parse memory
            for line in mem_result.stdout.split('\n'):
                if 'TotalVisibleMemorySize' in line:
                    total = int(line.split('=')[1].strip())
                elif 'FreePhysicalMemory' in line:
                    free = int(line.split('=')[1].strip())

            if 'total' in locals() and 'free' in locals():
                metrics["memory_percent"] = round(((total - free) / total) * 100, 2)

            return metrics

        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
            return {"memory_percent": 0, "cpu_percent": 0}

    @staticmethod
    def ensure_service_running() -> bool:
        """Verify detector is running as system service (NSSM).
        
        For deployment: This should be set up once with:
        nssm install VMManagerDetector python src/main.py
        nssm set VMManagerDetector AppDirectory C:\\path\\to\\guest-detector
        nssm start VMManagerDetector
        
        Returns:
            True if running as service
        """
        try:
            result = subprocess.run(
                ["nssm", "status", "VMManagerDetector"],
                capture_output=True,
                text=True,
                timeout=5
            )

            is_running = "SERVICE_RUNNING" in result.stdout
            logger.info(f"Service status: {'Running' if is_running else 'Not running'}")

            return is_running

        except Exception as e:
            logger.warning(f"Could not check service status: {e}")
            return False
