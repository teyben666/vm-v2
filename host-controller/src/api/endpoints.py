"""FastAPI endpoints for guest-host communication."""
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import logging
import os
from typing import Optional

from src import db
from src.hypervisor_plugin import get_hypervisor_plugin

logger = logging.getLogger(__name__)
app = FastAPI(title="VM Manager API")

# Configuration
MAX_FAILED_AUTH = int(os.getenv("MAX_FAILED_AUTH", 3))


class HeartbeatPayload(BaseModel):
    """Heartbeat payload from guest detector."""
    afk: bool
    afk_duration_minutes: int
    parsec_connected: bool
    memory_usage_percent: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class HeartbeatResponse(BaseModel):
    """Response to heartbeat with potential command."""
    status: str
    command: Optional[str] = None
    delay_seconds: Optional[int] = None


async def authenticate_detector(
    detector_id: str,
    secret_key: str
) -> dict:
    """Authenticate a detector by ID and secret key.
    
    Returns:
        VM dict if authenticated, raises HTTPException otherwise
    """
    vm = await db.get_vm(detector_id)
    
    if not vm:
        logger.warning(f"Authentication attempt for unknown detector: {detector_id}")
        raise HTTPException(status_code=404, detail="Detector not found")
    
    if vm["secret_key"] != secret_key:
        logger.warning(f"Invalid secret key for detector: {detector_id}")
        await db.record_failed_auth(detector_id)
        
        failed_count = await db.get_failed_auth_count(detector_id)
        if failed_count >= MAX_FAILED_AUTH:
            logger.error(f"Detector {detector_id} exceeded max auth attempts")
            raise HTTPException(status_code=403, detail="Max auth attempts exceeded")
        
        raise HTTPException(status_code=401, detail="Invalid secret key")
    
    # Clear failed auth on successful authentication
    await db.clear_failed_auth(detector_id)
    return vm


@app.post("/api/heartbeat", response_model=HeartbeatResponse)
async def receive_heartbeat(
    payload: HeartbeatPayload,
    x_detector_id: str = Header(...),
    x_vm_secret: str = Header(...)
):
    """Receive heartbeat from guest detector.
    
    Detects if VM is idle and pending shutdown.
    Returns command for detector to execute if any.
    """
    # Authenticate
    vm = await authenticate_detector(x_detector_id, x_vm_secret)
    
    # Update VM status to online
    await db.update_vm_status(x_detector_id, "online")
    
    logger.info(
        f"Heartbeat from {x_detector_id}: AFK={payload.afk} "
        f"({payload.afk_duration_minutes}min), Parsec={payload.parsec_connected}"
    )
    
    # Check if pending shutdown
    if vm["status"] == "pending_shutdown":
        logger.info(f"Sending shutdown command to {x_detector_id}")
        await db.update_vm_status(x_detector_id, "offline")
        return HeartbeatResponse(
            status="acknowledged",
            command="shutdown",
            delay_seconds=60
        )
    
    # Check for idle + disconnected for too long (handled by detector)
    if payload.afk and not payload.parsec_connected:
        if payload.afk_duration_minutes >= int(os.getenv("AFK_THRESHOLD_MINUTES", 60)):
            logger.warning(f"VM {x_detector_id} idle for {payload.afk_duration_minutes}min, notifying detector")
            return HeartbeatResponse(
                status="acknowledged",
                command="auto_shutdown_pending",
                delay_seconds=300  # 5 minute warning
            )
    
    return HeartbeatResponse(status="acknowledged")


@app.post("/api/alert")
async def receive_alert(
    request: Request,
    x_detector_id: str = Header(...),
    x_vm_secret: str = Header(...)
):
    """Receive an alert from guest detector.
    
    Used for special events like imminent shutdown.
    """
    vm = await authenticate_detector(x_detector_id, x_vm_secret)
    body = await request.json()
    
    alert_type = body.get("type", "unknown")
    message = body.get("message", "")
    
    logger.warning(f"Alert from {x_detector_id} ({alert_type}): {message}")
    
    # In a real implementation, forward to Telegram
    # For now, just log it
    
    return {"status": "received"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/vms")
async def list_vms(
    x_detector_id: str = Header(None),
    x_vm_secret: str = Header(None)
):
    """List all registered VMs (requires authentication)."""
    # Authenticate if both headers provided
    if x_detector_id and x_vm_secret:
        try:
            await authenticate_detector(x_detector_id, x_vm_secret)
        except HTTPException:
            raise
    else:
        # If headers missing, deny access
        raise HTTPException(status_code=401, detail="Authentication required")
    
    vms = await db.get_all_vms()
    return {"vms": vms, "count": len(vms)}


@app.get("/api/vms/{detector_id}")
async def get_vm_info(
    detector_id: str,
    x_vm_secret: str = Header(None)
):
    """Get info about a specific VM (requires authentication)."""
    if not x_vm_secret:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        vm = await authenticate_detector(detector_id, x_vm_secret)
    except HTTPException:
        raise
    
    return vm


async def setup_routes():
    """Initialize the API (called from main)."""
    logger.info("FastAPI routes initialized")
