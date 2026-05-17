# ============================================================
# Pydantic Models - SensorReading, DeviceStatus, HealthResponse
# ============================================================

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    id: Optional[int] = None
    device_id: str
    org_id: str
    site_id: str
    sensor: str
    value: float
    unit: str
    quality: int = 1
    ts: int
    seq: int
    fw_version: Optional[str] = None
    gateway_id: Optional[str] = None
    created_at: Optional[datetime] = None


class DeviceStatus(BaseModel):
    device_id: str
    status: str
    last_seen: Optional[int] = None
    rssi: Optional[int] = None
    heap_free: Optional[int] = None
    uptime_s: Optional[int] = None
    fw_version: Optional[str] = None
    org_id: Optional[str] = None
    site_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    mqtt_connected: bool
    db_status: str
    uptime_s: float
    readings_count: int
    devices_count: int