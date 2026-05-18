import asyncio
import threading


class EventBus:
    def __init__(self):
        self._queues: list[asyncio.Queue] = []
        self._lock = threading.Lock()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        with self._lock:
            self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        with self._lock:
            if q in self._queues:
                self._queues.remove(q)

    def publish(self, event: dict):
        with self._lock:
            for q in list(self._queues):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._queues)


bus = EventBus()