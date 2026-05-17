#!/usr/bin/env python3
# ============================================================
# Device Simulator - Full implementation per spec Section 5.3
# Critical: anomaly injection must make vibration_rms exceed 0.30g
# ============================================================

import argparse
import json
import random
import time
import uuid
from datetime import datetime

import paho.mqtt.client as mqtt


class DeviceSimulator:
    def __init__(self, org_id, site_id, device_id, mqtt_broker, mqtt_port, interval):
        self.org_id = org_id
        self.site_id = site_id
        self.device_id = device_id
        self.interval = interval
        self.seq = 0
        self.start_time = time.time()
        self.anomaly_triggered = False

        self.client = mqtt.Client(client_id=f"sim-{device_id}")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.client.connect(mqtt_broker, mqtt_port, keepalive=60)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[SIM] Connected to MQTT broker")
        else:
            print(f"[SIM] Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[SIM] Disconnected with code {rc}")

    def _generate_temperature(self):
        base = 22.0 + random.gauss(0, 2)
        return round(base + random.uniform(-0.5, 0.5), 2)

    def _generate_humidity(self):
        base = 55.0 + random.gauss(0, 5)
        return round(max(0, min(100, base + random.uniform(-2, 2))), 2)

    def _generate_vibration(self):
        elapsed = time.time() - self.start_time
        if not self.anomaly_triggered and elapsed > 30:
            self.anomaly_triggered = True

        if self.anomaly_triggered:
            vibration = random.uniform(0.35, 0.55)
        else:
            vibration = random.uniform(0.01, 0.08)

        return {
            "vibration_rms": round(vibration, 4),
            "vibration_peak": round(vibration * 1.5, 4)
        }

    def _generate_current(self):
        base = 5.0 + random.gauss(0, 0.5)
        return round(max(0, base + random.uniform(-0.3, 0.3)), 4)

    def _publish_reading(self, sensor, value, unit, quality=1):
        self.seq += 1
        topic = f"iot/{self.org_id}/{self.site_id}/{self.device_id}/{sensor}/raw"
        payload = {
            "device_id": self.device_id,
            "org_id": self.org_id,
            "site_id": self.site_id,
            "sensor": sensor,
            "value": value,
            "unit": unit,
            "quality": quality,
            "ts": int(time.time() * 1000),
            "seq": self.seq,
            "fw_version": "1.0.0-sim"
        }
        result = self.client.publish(topic, json.dumps(payload), qos=0)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[PUB] {topic} val={value} {unit}")
        else:
            print(f"[PUB] FAILED {topic}")

    def _publish_status(self):
        topic = f"iot/{self.org_id}/{self.site_id}/{self.device_id}/status"
        uptime = int(time.time() - self.start_time)
        payload = {
            "device_id": self.device_id,
            "status": "online",
            "rssi": random.randint(-70, -40),
            "heap_free": random.randint(100000, 200000),
            "uptime_s": uptime,
            "ts": int(time.time() * 1000),
            "fw_version": "1.0.0-sim"
        }
        self.client.publish(topic, json.dumps(payload), qos=1)
        print(f"[STATUS] heartbeat sent")

    def run(self):
        self.client.loop_start()
        time.sleep(1)

        status_count = 0
        while True:
            temperature = self._generate_temperature()
            self._publish_reading("temperature", temperature, "celsius")

            humidity = self._generate_humidity()
            self._publish_reading("humidity", humidity, "percent")

            vibration = self._generate_vibration()
            self._publish_reading("vibration_rms", vibration["vibration_rms"], "g")
            self._publish_reading("vibration_peak", vibration["vibration_peak"], "g")

            current = self._generate_current()
            self._publish_reading("current", current, "amps")

            status_count += 1
            if status_count >= 12:
                self._publish_status()
                status_count = 0

            time.sleep(self.interval)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="IoT Device Simulator")
    parser.add_argument("--devices", type=int, default=1, help="Number of devices to simulate")
    parser.add_argument("--interval", type=int, default=5, help="Publishing interval in seconds")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--org-id", default="acme", help="Organization ID")
    parser.add_argument("--site-id", default="test-site", help="Site ID")
    parser.add_argument("--anomaly", action="store_true", help="Enable anomaly injection after 30s")

    args = parser.parse_args()

    devices = []
    for i in range(args.devices):
        device_id = f"ESP32-{uuid.uuid4().hex[:8]}"
        simulator = DeviceSimulator(
            org_id=args.org_id,
            site_id=args.site_id,
            device_id=device_id,
            mqtt_broker=args.broker,
            mqtt_port=args.port,
            interval=args.interval
        )
        devices.append(simulator)
        print(f"[SIM] Started device {i+1}/{args.devices}: {device_id}")

    try:
        for sim in devices:
            sim.run()
    except KeyboardInterrupt:
        print("\n[SIM] Stopping...")
        for sim in devices:
            sim.stop()


if __name__ == "__main__":
    main()