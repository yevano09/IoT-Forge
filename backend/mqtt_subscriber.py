# ============================================================
# MQTT Subscriber - Background thread
# Subscribe to iot/#, route to DB + EventBus
# Thread-safe bridge to async loop via asyncio.run_coroutine_threadsafe
# ============================================================

import json
import threading
import asyncio
from typing import Callable, List, Any

import paho.mqtt.client as mqtt
import metrics


class MQTTPSubscriber:
    def __init__(self, broker_host: str, broker_port: int, database, event_callbacks: List[Callable] = None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.database = database
        self.event_callbacks = event_callbacks or []
        self._loop = None
        self._running = False

        self.client = mqtt.Client(client_id="backend-subscriber")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected to broker")
            client.subscribe("iot/#")
        else:
            print(f"[MQTT] Connection failed: {rc}")
            metrics.mqtt_connection_errors.inc()

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            metrics.record_mqtt_message(topic)

            if self._loop and self.database:
                asyncio.run_coroutine_threadsafe(
                    self._process_message(topic, payload),
                    self._loop
                )
        except json.JSONDecodeError:
            print(f"[MQTT] Invalid JSON: {msg.payload}")
        except Exception as e:
            print(f"[MQTT] Message processing error: {e}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] Disconnected: {rc}")
        if rc != 0:
            metrics.mqtt_connection_errors.inc()

    async def _process_message(self, topic: str, payload: dict):
        try:
            if "/status" in topic:
                await self.database.update_device_status(payload)
                device_id = payload.get("device_id", "unknown")
                status = payload.get("status", "offline")
                metrics.set_device_online(device_id, status == "online")
            else:
                await self.database.insert_reading(payload)

                device_id = payload.get("device_id", "unknown")
                org_id = payload.get("org_id", "unknown")
                site_id = payload.get("site_id", "unknown")
                sensor = payload.get("sensor", "unknown")
                value = payload.get("value", 0)
                unit = payload.get("unit", "")

                metrics.record_sensor_reading(device_id, org_id, site_id, sensor, value, unit)

            metrics.mqtt_messages_processed.inc()

            for callback in self.event_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(topic, payload)
                    else:
                        callback(topic, payload)
                except Exception as e:
                    print(f"[MQTT] Event callback error: {e}")
        except Exception as e:
            print(f"[MQTT] Process error: {e}")

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def start(self):
        self._running = True
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()
        print(f"[MQTT] Subscriber started")

    def stop(self):
        self._running = False
        self.client.loop_stop()
        self.client.disconnect()
        print(f"[MQTT] Subscriber stopped")

    def add_event_callback(self, callback: Callable):
        self.event_callbacks.append(callback)