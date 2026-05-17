# ============================================================
# Devices Router - GET /api/v1/devices
# ============================================================

from typing import Optional
from fastapi import APIRouter, Depends
from models import DeviceStatus

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


def get_database():
    from main import get_db
    return get_db()


@router.get("", response_model=list[DeviceStatus])
async def list_devices(db=Depends(get_database)):
    devices = await db.get_devices()
    return [
        DeviceStatus(
            device_id=d.get("device_id"),
            status=d.get("status", "unknown"),
            last_seen=d.get("last_seen"),
            rssi=d.get("rssi"),
            heap_free=d.get("heap_free"),
            uptime_s=d.get("uptime_s"),
            fw_version=d.get("fw_version"),
            org_id=d.get("org_id"),
            site_id=d.get("site_id")
        )
        for d in devices
    ]


@router.get("/{device_id}", response_model=DeviceStatus)
async def get_device(device_id: str, db=Depends(get_database)):
    device = await db.get_device(device_id)
    if not device:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceStatus(
        device_id=device.get("device_id"),
        status=device.get("status", "unknown"),
        last_seen=device.get("last_seen"),
        rssi=device.get("rssi"),
        heap_free=device.get("heap_free"),
        uptime_s=device.get("uptime_s"),
        fw_version=device.get("fw_version"),
        org_id=device.get("org_id"),
        site_id=device.get("site_id")
    )