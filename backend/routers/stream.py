import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.event_bus import bus

router = APIRouter()


@router.get("/stream")
async def stream():
    """
    Server-Sent Events stream. Pushes every new sensor reading in real time.

    Each event:  data: {JSON payload}\n\n
    Keepalive:   : keepalive\n\n   (sent every 30s to prevent proxy timeouts)

    Connect:  EventSource('http://localhost:8000/api/v1/stream')
    """
    q = bus.subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        }
    )
