# ============================================================
# Stream Router - GET /api/v1/stream → SSE
# Keepalive every 30s, clean up on disconnect
# ============================================================

import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/stream", tags=["stream"])

_active_streams: Set[asyncio.Queue] = set()


async def event_generator():
    queue: asyncio.Queue = asyncio.Queue()
    _active_streams.add(queue)

    try:
        async def send_event(data: dict, event: str = "message"):
            await queue.put(f"event: {event}\ndata: {json.dumps(data)}\n\n")

        def mqtt_callback(topic: str, payload: dict):
            asyncio.create_task(send_event({"topic": topic, "payload": payload}, "reading"))

        from main import get_mqtt_subscriber
        subscriber = get_mqtt_subscriber()
        if subscriber:
            subscriber.add_event_callback(mqtt_callback)

        send_event({"status": "connected"}, "status")

        keepalive_task = None

        async def keepalive():
            while True:
                await asyncio.sleep(30)
                await queue.put(": keepalive\n\n")

        keepalive_task = asyncio.create_task(keepalive())

        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=60)
                yield message
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        if 'keepalive_task' in locals() and keepalive_task:
            keepalive_task.cancel()
        _active_streams.discard(queue)


@router.get("")
async def stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")