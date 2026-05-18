import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.database        import db
from backend.metrics         import get_metrics, record_request
from backend.mqtt_subscriber import subscriber
from backend.routers        import devices, readings, stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
)
log = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    log.info("Initialising database...")
    await db.init()
    log.info("Starting MQTT subscriber...")
    loop = asyncio.get_event_loop()
    subscriber.start(loop)
    log.info("Edge Sense API ready")
    yield
    log.info("Stopping MQTT subscriber...")
    subscriber.stop()
    log.info("Shutdown complete")


app = FastAPI(
    title="IoT Forge — Edge Sense API",
    description="Real-time IoT sensor data ingestion, storage, and streaming",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(devices.router,  prefix="/api/v1")
app.include_router(readings.router, prefix="/api/v1")
app.include_router(stream.router,   prefix="/api/v1")


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(get_metrics())


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    import time as t
    start = t.time()
    response = await call_next(request)
    duration = t.time() - start
    record_request(request.method, request.url.path, response.status_code)
    return response


@app.get("/api/v1/health")
async def health():
    count = await db.device_count()
    return {"status": "ok", "ts": int(time.time() * 1000), "device_count": count}