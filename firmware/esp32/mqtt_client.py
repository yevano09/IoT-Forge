# ============================================================
# MQTTClient - MQTT wrapper with TLS support and exponential backoff
# publish() returns False on error, marks self as disconnected
# ============================================================

import utime
import ujson


class MQTTClient:
    def __init__(self, config, device_id):
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 1883)
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.keepalive = config.get("keepalive", 60)
        self.ssl = config.get("ssl", None)
        self.device_id = device_id

        self._client = None
        self._connected = False
        self._on_message = None
        self._subscribe_topics = []

        self._backoff_base = 1
        self._backoff_max = 60
        self._backoff = self._backoff_base

    def connect(self, on_message, subscribe_topics):
        from umqtt.robust import MQTTClient as UMQTTClient

        self._on_message = on_message
        self._subscribe_topics = subscribe_topics

        client_id = f"esp32-{self.device_id}"
        self._client = MQTTClient(client_id, self.host, self.port,
                                  keepalive=self.keepalive)

        if self.username and self.password:
            self._client.set_auth(self.username, self.password)

        if self.ssl:
            self._client.set_ca(cafile=self.ssl.get("cafile"))

        self._client.set_callback(self._handle_message)

        try:
            self._client.connect()
            self._connected = True
            self._backoff = self._backoff_base

            for topic in subscribe_topics:
                self._client.subscribe(topic)
                print(f"[MQTT] subscribed to {topic}")

            print(f"[MQTT] connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[MQTT] connect failed: {e}")
            self._connected = False
            return False

    def _handle_message(self, topic, msg):
        if self._on_message:
            try:
                self._on_message(topic, msg)
            except Exception as e:
                print(f"[MQTT] message handler error: {e}")

    def publish(self, topic, payload, qos=0):
        if not self._connected or not self._client:
            return False
        try:
            self._client.publish(topic, payload, qos=qos)
            return True
        except Exception as e:
            print(f"[MQTT] publish error: {e}")
            self._connected = False
            return False

    def is_connected(self):
        return self._connected

    def reconnect(self):
        self._connected = False
        wait_time = self._backoff
        print(f"[MQTT] reconnecting in {wait_time}s...")
        utime.sleep(wait_time)

        try:
            self._client.connect()
            self._connected = True
            self._backoff = self._backoff_base

            for topic in self._subscribe_topics:
                self._client.subscribe(topic)
            print("[MQTT] reconnected")
            return True
        except Exception as e:
            print(f"[MQTT] reconnect failed: {e}")
            self._backoff = min(self._backoff * 2, self._backoff_max)
            return False

    def disconnect(self):
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
        self._connected = False