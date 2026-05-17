# ============================================================
# Readings Router - GET /api/v1/readings, GET /api/v1/readings/latest
# ============================================================

from typing import Optional
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/api/v1/readings", tags=["readings"])


def get_database():
    from main import get_db
    return get_db()


@router.get("")
async def get_readings(
    device_id: Optional[str] = Query(None),
    sensor: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db=Depends(get_database)
):
    readings = await db.get_readings(
        device_id=device_id,
        sensor=sensor,
        limit=limit,
        offset=offset
    )
    return {"readings": readings, "count": len(readings)}


@router.get("/latest")
async def get_latest_readings(
    device_id: Optional[str] = Query(None),
    db=Depends(get_database)
):
    readings = await db.get_latest_readings(device_id=device_id)
    return {"readings": readings, "count": len(readings)}


@router.get("/{device_id}/{sensor}")
async def get_sensor_reading(
    device_id: str,
    sensor: str,
    limit: int = Query(50, ge=1, le=500),
    db=Depends(get_database)
):
    readings = await db.get_readings(
        device_id=device_id,
        sensor=sensor,
        limit=limit
    )
    return {"device_id": device_id, "sensor": sensor, "readings": readings}