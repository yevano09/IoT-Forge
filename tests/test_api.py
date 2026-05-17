# ============================================================
# Test API - Use httpx AsyncClient
# ============================================================

import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_healthy(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "uptime_s" in data
            assert "readings_count" in data
            assert "devices_count" in data


class TestDevicesEndpoint:
    @pytest.mark.asyncio
    async def test_list_devices_returns_array(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/devices")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_single_device_not_found(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/devices/nonexistent-device")

            assert response.status_code == 404


class TestReadingsEndpoint:
    @pytest.mark.asyncio
    async def test_get_readings_returns_data(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/readings")

            assert response.status_code == 200
            data = response.json()
            assert "readings" in data
            assert "count" in data

    @pytest.mark.asyncio
    async def test_get_readings_with_filters(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/readings?device_id=test-device&sensor=temperature&limit=10")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_latest_readings(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/readings/latest")

            assert response.status_code == 200
            data = response.json()
            assert "readings" in data
            assert "count" in data

    @pytest.mark.asyncio
    async def test_get_device_sensor_readings(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/readings/test-device/temperature")

            assert response.status_code == 200
            data = response.json()
            assert "device_id" in data
            assert "sensor" in data
            assert "readings" in data


class TestStreamEndpoint:
    @pytest.mark.asyncio
    async def test_stream_endpoint_exists(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/stream")

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")


class TestCORS:
    @pytest.mark.asyncio
    async def test_cors_headers_present(self):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})

            assert "access-control-allow-origin" in response.headers