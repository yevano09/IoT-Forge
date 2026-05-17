# ============================================================
# Backend Main - Wire all routers
# Lifespan: init DB + start subscriber. CORS. /health endpoint.
# ============================================================

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from database import Database
from mqtt_subscriber import MQTTPSubscriber
from models import HealthResponse
from routers import devices, readings, stream
import metrics

_db: Database = None
_mqtt_subscriber: MQTTPSubscriber = None


def get_db():
    return _db


def get_mqtt_subscriber():
    return _mqtt_subscriber


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db, _mqtt_subscriber

    db_path = os.environ.get("DB_PATH", "iot_data.db")
    _db = Database(db_path)
    await _db.init()

    mqtt_host = os.environ.get("MQTT_HOST", "localhost")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    _mqtt_subscriber = MQTTPSubscriber(mqtt_host, mqtt_port, _db)
    _mqtt_subscriber.set_loop(asyncio.get_event_loop())
    _mqtt_subscriber.start()

    print("[APP] Started")
    yield

    if _mqtt_subscriber:
        _mqtt_subscriber.stop()
    if _db:
        await _db.close()
    print("[APP] Stopped")


app = FastAPI(title="IoT Forge API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router)
app.include_router(readings.router)
app.include_router(stream.router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    mqtt_connected = _mqtt_subscriber.client.is_connected() if _mqtt_subscriber else False
    readings_count = await _db.get_readings_count()
    devices_count = await _db.get_devices_count()

    metrics.db_readings_count.set(readings_count)

    return HealthResponse(
        status="healthy",
        mqtt_connected=mqtt_connected,
        db_status="connected",
        uptime_s=_db.get_uptime(),
        readings_count=readings_count,
        devices_count=devices_count
    )


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(content=metrics.get_metrics(), media_type="text/plain")


@app.get("/")
async def root():
    return {"message": "IoT Forge API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)