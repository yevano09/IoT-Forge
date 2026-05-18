from fastapi import APIRouter, Query
from typing import Optional
from backend.database import db

router = APIRouter()


@router.get("/readings")
async def get_readings(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    sensor:    Optional[str] = Query(None, description="Filter by sensor type"),
    limit:     int           = Query(200, ge=1, le=5000),
    since_ts:  Optional[int] = Query(None, description="Only readings >= this Unix ms timestamp"),
):
    return await db.get_readings(device_id=device_id, sensor=sensor, limit=limit, since_ts=since_ts)


@router.get("/readings/latest")
async def latest_readings():
    return await db.get_latest_readings()