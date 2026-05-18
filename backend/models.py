from pydantic import BaseModel
from typing import Optional


class SensorReading(BaseModel):
    device_id:   str
    sensor:      str
    value:       Optional[float] = None
    unit:        str             = ""
    quality:     int             = 1
    ts:          int
    fw_version:  Optional[str]   = None


class DeviceStatus(BaseModel):
    device_id:  str
    org_id:     Optional[str] = None
    site_id:    Optional[str] = None
    status:     str           = "unknown"
    last_seen:  Optional[int] = None
    fw_version: Optional[str] = None
    rssi:       Optional[int] = None


class HealthResponse(BaseModel):
    status:       str
    ts:           int
    device_count: int