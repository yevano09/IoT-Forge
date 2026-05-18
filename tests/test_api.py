import os
os.environ["DB_PATH"] = ":memory:"

import time
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.main     import app
from backend.database import db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await db.init()
    yield
    await db.close()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "ts" in data
    assert "device_count" in data


@pytest.mark.asyncio
async def test_get_devices_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/devices")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_insert_and_retrieve_reading():
    payload = {
        "device_id": "TEST-001", "org_id": "test", "site_id": "lab",
        "sensor": "temperature", "value": 25.5, "unit": "celsius",
        "quality": 1, "ts": int(time.time() * 1000), "seq": 1, "fw_version": "1.0.0"
    }
    await db.insert_reading(payload)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/readings", params={"device_id": "TEST-001"})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["sensor"] == "temperature"
    assert rows[0]["value"] == 25.5


@pytest.mark.asyncio
async def test_latest_readings_one_per_sensor():
    base_ts = int(time.time() * 1000)
    for i, val in enumerate([20.0, 21.0, 22.0]):
        await db.insert_reading({
            "device_id": "TEST-002", "sensor": "temperature",
            "value": val, "unit": "celsius", "quality": 1,
            "ts": base_ts + i * 1000
        })
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/readings/latest")
    assert r.status_code == 200
    rows = r.json()
    sensor_rows = [row for row in rows if row["device_id"] == "TEST-002"]
    assert len(sensor_rows) == 1
    assert sensor_rows[0]["value"] == 22.0


@pytest.mark.asyncio
async def test_sse_stream_connects():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/stream", params={"max_events": 1, "keepalive": 0.1})
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]