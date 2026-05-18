import asyncio
import json
import logging
import time
import paho.mqtt.client as mqtt

log = logging.getLogger("mqtt_sub")


async def _handle_status(payload: dict):
    from backend.database import db
    from backend.metrics import set_device_online, mqtt_messages_processed
    await db.upsert_device(payload)
    set_device_online(payload.get("device_id", ""), True)
    mqtt_messages_processed.inc()


async def _handle_raw(payload: dict):
    from backend.database import db
    from backend.metrics import record_sensor_reading, mqtt_messages_processed, db_readings_count
    from backend.event_bus import bus
    await db.insert_reading(payload)
    bus.publish(payload)
    record_sensor_reading(
        payload.get("device_id", ""),
        payload.get("org_id", ""),
        payload.get("site_id", ""),
        payload.get("sensor", ""),
        payload.get("value", 0),
        payload.get("unit", ""),
    )
    count = await db.reading_count()
    db_readings_count.set(count)
    mqtt_messages_processed.inc()


def _on_mqtt_message(topic: str, payload: dict, loop: asyncio.AbstractEventLoop):
    from backend.metrics import record_mqtt_message
    record_mqtt_message(topic)
    if "/status" in topic:
        asyncio.run_coroutine_threadsafe(_handle_status(payload), loop)
    elif "/raw" in topic:
        asyncio.run_coroutine_threadsafe(_handle_raw(payload), loop)


class MQTTSubscriber:
    def __init__(self, host: str = "localhost", port: int = 1883):
        self.host = host
        self.port = port
        self._client = mqtt.Client(client_id="edge-sense-backend", protocol=mqtt.MQTTv311)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._loop: asyncio.AbstractEventLoop | None = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("iot/#", qos=0)
            log.info(f"MQTT subscriber connected  broker={self.host}:{self.port}")
        else:
            log.error(f"MQTT subscriber connect failed  rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            log.warning(f"Bad payload on {msg.topic}: {e}")
            return
        if self._loop is not None:
            _on_mqtt_message(msg.topic, payload, self._loop)

    def start(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        import os
        host = os.environ.get("MQTT_HOST", self.host)
        port = int(os.environ.get("MQTT_PORT", self.port))
        self._client.connect_async(host, port, keepalive=60)
        self._client.loop_start()
        log.info(f"MQTT subscriber starting  host={host}:{port}")

    def stop(self):
        self._client.loop_stop()
        self._client.disconnect()
        log.info("MQTT subscriber stopped")


subscriber = MQTTSubscriber()