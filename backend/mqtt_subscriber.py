import asyncio, json, logging, time
import paho.mqtt.client as mqtt
from backend.database  import db
from backend.event_bus import bus
from backend.metrics   import (
    set_device_online, record_sensor_reading, record_mqtt_message,
    mqtt_messages_processed, database_readings_count, database_devices_count
)

log = logging.getLogger("mqtt_sub")


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
        topic = msg.topic

        if topic == "iot/healthcheck":
            return

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            log.warning(f"Bad payload on {msg.topic}: {e}")
            return

        record_mqtt_message(topic)

        if self._loop is None:
            return

        if "/status" in topic:
            asyncio.run_coroutine_threadsafe(
                self._handle_status(payload), self._loop
            )
        elif "/raw" in topic:
            asyncio.run_coroutine_threadsafe(
                self._handle_raw(topic, payload), self._loop
            )

    async def _handle_status(self, payload: dict):
        device_id = payload.get("device_id", "")
        await db.upsert_device(payload)
        set_device_online(device_id, True)
        mqtt_messages_processed.inc()
        log.info(f"Processed status  device={device_id}")

    async def _handle_raw(self, topic: str, payload: dict):
        device_id = payload.get("device_id", "")
        sensor = payload.get("sensor", "")
        value = payload.get("value", 0)
        try:
            await db.insert_reading(payload)
            bus.publish(payload)
            record_sensor_reading(
                device_id,
                payload.get("org_id", ""),
                payload.get("site_id", ""),
                sensor,
                value,
                payload.get("unit", ""),
            )
            count = await db.reading_count() if hasattr(db, 'reading_count') else 0
            database_readings_count.set(count)
            mqtt_messages_processed.inc()
        except Exception:
            log.exception(f"_handle_raw FAILED  device={device_id}  sensor={sensor}")
            mqtt_messages_processed.inc()

    def start(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        host = __import__("os").environ.get("MQTT_HOST", self.host)
        port = int(__import__("os").environ.get("MQTT_PORT", self.port))
        self._client.connect_async(host, port, keepalive=60)
        self._client.loop_start()
        log.info(f"MQTT subscriber starting  host={host}:{port}")

    def stop(self):
        self._client.loop_stop()
        self._client.disconnect()
        log.info("MQTT subscriber stopped")


subscriber = MQTTSubscriber()
