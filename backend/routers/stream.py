import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.event_bus import bus

router = APIRouter()


@router.get("/stream")
async def stream(max_events: int = 0, keepalive: float = 30.0):
    q = bus.subscribe()
    sent = 0

    async def event_generator():
        nonlocal sent
        try:
            while max_events == 0 or sent < max_events:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=keepalive)
                    sent += 1
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    sent += 1
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