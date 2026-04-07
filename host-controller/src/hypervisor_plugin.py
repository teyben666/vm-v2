"""Hyper-V specific hypervisor plugin for VM management."""
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HyperVPlugin:
    """Interface to Hyper-V for VM control operations."""

    @staticmethod
    def start_vm(vm_name: str) -> tuple[bool, str]:
        """Start a VM using Hyper-V PowerShell commands.
        
        Args:
            vm_name: The name of the VM in Hyper-V
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            cmd = f"Start-VM -Name '{vm_name}' -ErrorAction Stop"
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully started VM: {vm_name}")
                return True, f"VM '{vm_name}' started successfully"
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Failed to start VM {vm_name}: {error_msg}")
                return False, f"Failed to start VM: {error_msg}"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout starting VM: {vm_name}")
            return False, "Operation timed out"
        except Exception as e:
            logger.error(f"Exception starting VM {vm_name}: {str(e)}")
            return False, f"Exception: {str(e)}"

    @staticmethod
    def stop_vm(vm_name: str, force: bool = False) -> tuple[bool, str]:
        """Stop a VM using Hyper-V PowerShell commands.
        
        Args:
            vm_name: The name of the VM in Hyper-V
            force: If True, perform a hard shutdown (TurnOff)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if force:
                cmd = f"Stop-VM -Name '{vm_name}' -TurnOff -Force -ErrorAction Stop"
                action = "force stopped"
            else:
                cmd = f"Stop-VM -Name '{vm_name}' -Force -ErrorAction Stop"
                action = "stopped"
                
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully {action} VM: {vm_name}")
                return True, f"VM '{vm_name}' {action} successfully"
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Failed to stop VM {vm_name}: {error_msg}")
                return False, f"Failed to stop VM: {error_msg}"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout stopping VM: {vm_name}")
            return False, "Operation timed out"
        except Exception as e:
            logger.error(f"Exception stopping VM {vm_name}: {str(e)}")
            return False, f"Exception: {str(e)}"

    @staticmethod
    def get_vm_state(vm_name: str) -> Optional[str]:
        """Check the current state of a VM.
        
        Args:
            vm_name: The name of the VM in Hyper-V
            
        Returns:
            VM state string or None if error
        """
        try:
            cmd = f"Get-VM -Name '{vm_name}' | Select-Object -ExpandProperty State"
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                state = result.stdout.strip()
                return state
            else:
                logger.warning(f"Could not get state of VM {vm_name}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting VM state {vm_name}: {str(e)}")
            return None

    @staticmethod
    def list_vms() -> list[str]:
        """List all VMs on the Hyper-V host.
        
        Returns:
            List of VM names
        """
        try:
            cmd = "Get-VM | Select-Object -ExpandProperty Name"
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                vms = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                return vms
            else:
                logger.error(f"Failed to list VMs: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Exception listing VMs: {str(e)}")
            return []


# Factory function for getting the right hypervisor plugin
def get_hypervisor_plugin():
    """Return the configured hypervisor plugin."""
    return HyperVPlugin()
