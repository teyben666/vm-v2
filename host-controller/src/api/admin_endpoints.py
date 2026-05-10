"""Admin HTTP API for META:GEN (and other server-side clients).

Auth: Authorization: Bearer <VM_HTTP_ADMIN_TOKEN>
Does not replace Telegram; guest /api/heartbeat unchanged.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, Body, Header, HTTPException

from src import db
from src.hypervisor_plugin import get_hypervisor_plugin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

_ADMIN_TOKEN = os.getenv("VM_HTTP_ADMIN_TOKEN", "").strip()


def _require_admin_bearer(authorization: Optional[str]) -> None:
    if not _ADMIN_TOKEN:
        logger.warning("VM_HTTP_ADMIN_TOKEN is not set; admin HTTP API disabled")
        raise HTTPException(status_code=503, detail="Admin HTTP API not configured on host")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization")
    token = authorization[7:].strip()
    if token != _ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


def _sanitize_vm(row: dict) -> dict:
    """Strip secrets for dashboard consumers."""
    out = {k: v for k, v in row.items() if k != "secret_key"}
    return out


@router.get("/vms")
async def admin_list_vms(authorization: Optional[str] = Header(None)) -> dict:
    """List all VMs (no secret_key). Requires Bearer VM_HTTP_ADMIN_TOKEN."""
    _require_admin_bearer(authorization)
    vms: List[dict] = await db.get_all_vms()
    safe = [_sanitize_vm(dict(r)) for r in vms]
    online = sum(1 for v in safe if v.get("status") == "online")
    return {"vms": safe, "count": len(safe), "online": online}


@router.get("/health")
async def admin_health(authorization: Optional[str] = Header(None)) -> dict:
    """Lightweight auth check for proxies."""
    _require_admin_bearer(authorization)
    return {"status": "ok"}


class StopVmBody(BaseModel):
    force: bool = False


@router.post("/vm/{detector_id}/start")
async def admin_vm_start(detector_id: str, authorization: Optional[str] = Header(None)) -> dict:
    """Power on VM via hypervisor (e.g. Hyper-V Start-VM)."""
    _require_admin_bearer(authorization)
    vm = await db.get_vm(detector_id)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    plugin = get_hypervisor_plugin()
    ok, msg = plugin.start_vm(vm["hypervisor_name"])
    if ok:
        await db.update_vm_status(detector_id, "online")
    return {"ok": ok, "message": msg}


@router.post("/vm/{detector_id}/stop")
async def admin_vm_stop(
    detector_id: str,
    authorization: Optional[str] = Header(None),
    body: StopVmBody = Body(default_factory=StopVmBody),
) -> dict:
    """Graceful: mark pending_shutdown (guest handles on heartbeat). Force: TurnOff via hypervisor."""
    _require_admin_bearer(authorization)
    vm = await db.get_vm(detector_id)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    if not body.force:
        await db.set_vm_pending_shutdown(detector_id)
        return {
            "ok": True,
            "mode": "graceful",
            "message": "Shutdown queued for next guest heartbeat",
        }
    plugin = get_hypervisor_plugin()
    ok, msg = plugin.stop_vm(vm["hypervisor_name"], force=True)
    if ok:
        await db.update_vm_status(detector_id, "offline")
    return {"ok": ok, "mode": "force", "message": msg}
