#!/usr/bin/env python3
# ============================================================
# RPi Gateway - Full implementation per spec Section 5.2
# Must: enrich payloads, buffer when offline, flush on reconnect,
# expose /health and /devices
# ============================================================

import json
import os
import sys
import threading
import time
from datetime import datetime

import yaml
import paho.mqtt.client as mqtt
from http.server import HTTPServer, BaseHTTPRequestHandler


class LocalBuffer:
    def __init__(self, max_records=1000, file_path="/tmp/gateway_buffer.json"):
        self.max_records = max_records
        self.file_path = file_path
        self.records = []
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.records = json.load(f)
            except Exception:
                self.records = []

    def _save(self):
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.records, f)
        except Exception:
            pass

    def add(self, payload):
        if len(self.records) >= self.max_records:
            self.records.pop(0)
        self.records.append(payload)
        self._save()

    def get_all(self):
        return list(self.records)

    def clear(self):
        self.records = []
        self._save()


class Gateway:
    def __init__(self, config_path="gateway_config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        gateway_cfg = self.config.get("gateway", {})
        self.device_id = gateway_cfg.get("device_id", "rpi-gateway-001")
        self.org_id = gateway_cfg.get("org_id", "acme")
        self.site_id = gateway_cfg.get("site_id", "default")

        local_broker = self.config.get("local_broker", {})
        self.local_host = local_broker.get("host", "localhost")
        self.local_port = local_broker.get("port", 1883)

        upstream_broker = self.config.get("upstream_broker", {})
        self.upstream_host = upstream_broker.get("host", "")
        self.upstream_port = upstream_broker.get("port", 1883)
        self.upstream_user = upstream_broker.get("username", "")
        self.upstream_pass = upstream_broker.get("password", "")

        buffer_cfg = self.config.get("buffer", {})
        self.buffer = LocalBuffer(
            max_records=buffer_cfg.get("max_records", 1000),
            file_path=buffer_cfg.get("file_path", "/tmp/gateway_buffer.json")
        )

        self.devices = {}
        self.last_heartbeat = {}

        self.local_client = mqtt.Client(client_id=f"gateway-{self.device_id}")
        self.local_client.on_connect = self._on_local_connect
        self.local_client.on_message = self._on_local_message
        self.local_client.on_disconnect = self._on_local_disconnect

        self.upstream_client = None
        if self.upstream_host:
            self.upstream_client = mqtt.Client(client_id=f"gateway-upstream-{self.device_id}")
            self.upstream_client.on_connect = self._on_upstream_connect
            self.upstream_client.on_disconnect = self._on_upstream_disconnect

    def _on_local_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[LOCAL] Connected to local broker")
            client.subscribe("iot/#")
        else:
            print(f"[LOCAL] Connection failed: {rc}")

    def _on_local_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic

            if "/status" in topic:
                device_id = payload.get("device_id")
                if device_id:
                    self.devices[device_id] = {
                        "last_seen": time.time(),
                        "status": payload.get("status", "unknown"),
                        "rssi": payload.get("rssi"),
                        "uptime_s": payload.get("uptime_s")
                    }
                    self.last_heartbeat[device_id] = time.time()
            else:
                enriched_payload = self._enrich_payload(payload)
                topic_parts = topic.split("/")

                if len(topic_parts) >= 5:
                    upstream_topic = f"iot/{self.org_id}/{self.site_id}/gateway/{topic_parts[-1]}"
                else:
                    upstream_topic = topic

                if self.upstream_client and self.upstream_client.is_connected():
                    self.upstream_client.publish(upstream_topic, json.dumps(enriched_payload))
                    print(f"[UPSTREAM] forwarded to {upstream_topic}")
                else:
                    enriched_payload["_buffered_at"] = time.time()
                    self.buffer.add(enriched_payload)
                    print(f"[BUFFER] offline - buffered message")

        except json.JSONDecodeError:
            print(f"[LOCAL] Invalid JSON: {msg.payload}")

    def _on_local_disconnect(self, client, userdata, rc):
        print(f"[LOCAL] Disconnected: {rc}")

    def _on_upstream_connect(self, client, userdata, rc):
        if rc == 0:
            print(f"[UPSTREAM] Connected to upstream broker")
            self._flush_buffer()
        else:
            print(f"[UPSTREAM] Connection failed: {rc}")

    def _on_upstream_disconnect(self, client, userdata, rc):
        print(f"[UPSTREAM] Disconnected: {rc}")

    def _enrich_payload(self, payload):
        return {
            **payload,
            "gateway_id": self.device_id,
            "gateway_ts": int(time.time() * 1000),
            "org_id": self.org_id,
            "site_id": self.site_id
        }

    def _flush_buffer(self):
        records = self.buffer.get_all()
        if not records:
            return
        print(f"[BUFFER] flushing {len(records)} buffered messages")
        for rec in records:
            topic = f"iot/{self.org_id}/{self.site_id}/gateway/buffered"
            self.upstream_client.publish(topic, json.dumps(rec))
        self.buffer.clear()

    def start(self):
        print(f"[GATEWAY] Starting...")
        self.local_client.connect(self.local_host, self.local_port, keepalive=60)
        self.local_client.loop_start()

        if self.upstream_client:
            if self.upstream_user and self.upstream_pass:
                self.upstream_client.username_pw_set(self.upstream_user, self.upstream_pass)
            self.upstream_client.connect(self.upstream_host, self.upstream_port, keepalive=60)
            self.upstream_client.loop_start()

        health_server = HealthServer(self, self.config.get("health", {}).get("port", 8080))
        health_thread = threading.Thread(target=health_server.serve_forever)
        health_thread.daemon = True
        health_thread.start()

        print(f"[GATEWAY] Running. Health endpoint on port {health_server.server.server_address[1]}")

        while True:
            time.sleep(10)
            self._cleanup_stale_devices()

    def _cleanup_stale_devices(self):
        now = time.time()
        stale_threshold = 120
        stale = [d for d, info in self.devices.items()
                 if now - info.get("last_seen", 0) > stale_threshold]
        for d in stale:
            self.devices[d]["status"] = "offline"


class HealthHandler(BaseHTTPRequestHandler):
    def __init__(self, gateway, *args, **kwargs):
        self.gateway = gateway
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "gateway_id": self.gateway.device_id,
                "devices": len(self.gateway.devices),
                "buffered": len(self.gateway.buffer)
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/devices":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "devices": self.gateway.devices
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class HealthServer:
    def __init__(self, gateway, port):
        self.gateway = gateway
        self.server = HTTPServer(("", port), lambda *args, **kwargs: HealthHandler(gateway, *args, **kwargs))

    def serve_forever(self):
        self.server.serve_forever()


def main():
    config_path = "gateway_config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    gateway = Gateway(config_path)
    gateway.start()


if __name__ == "__main__":
    main()