#!/usr/bin/env python3
# ============================================================
# Device Simulator
# Generates realistic, time-correlated sensor data for
# multiple IoT devices connected to an MQTT broker.
# ============================================================

import argparse
import json
import math
import random
import signal
import sys
import threading
import time


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def _load_paho():
    try:
        import paho.mqtt.client as mqtt
        return mqtt
    except ImportError:
        return None


mqtt = _load_paho()


class SensorModel:
    def __init__(self, device_id: str, seed: int):
        self.device_id = device_id
        self.t = 0
        self.anomaly_active = False
        self._rng = random.Random(seed)
        self.temp_base = 28.0 + self._rng.uniform(-5, 5)
        self.hum_base = 60.0 + self._rng.uniform(-10, 10)
        self.vib_base = 0.05 + self._rng.uniform(0, 0.03)
        self.curr_base = 8.0 + self._rng.uniform(-2, 2)

    def temperature(self) -> float:
        drift = 2.0 * math.sin(self.t / 120)
        noise = self._rng.gauss(0, 0.3)
        spike = self._rng.gauss(5, 1) if self.anomaly_active else 0
        return round(self.temp_base + drift + noise + spike, 2)

    def humidity(self) -> float:
        drift = 2.0 * math.sin(self.t / 120)
        delta = self.temp_base + drift - self.temp_base
        noise = self._rng.gauss(0, 0.5)
        return round(clamp(self.hum_base + 0.8 * delta + noise, 5, 98), 2)

    def vibration_rms(self) -> float:
        noise = self._rng.gauss(0, 0.005)
        spike = self._rng.gauss(0.35, 0.05) if self.anomaly_active else 0
        return round(max(0, self.vib_base + noise + spike), 4)

    def vibration_peak(self) -> float:
        return round(self.vibration_rms() * self._rng.uniform(1.5, 2.5), 4)

    def motor_current(self) -> float:
        noise = self._rng.gauss(0, 0.2)
        surge = self._rng.gauss(4, 0.5) if self.anomaly_active else 0
        return round(max(0, self.curr_base + noise + surge), 3)

    def trigger_anomaly(self):
        self.anomaly_active = True
        print(f"[SIM] ANOMALY injected on {self.device_id}")

    def tick(self):
        self.t += 1


class SimDevice(threading.Thread):
    def __init__(self, device_id: str, seed: int, inject_anomaly: bool):
        super().__init__(daemon=True)
        self.device_id = device_id
        self.model = SensorModel(device_id, seed)
        self.inject_anomaly = inject_anomaly
        self.seq = 0
        self.start_time = time.time()
        self._connected = False
        self._stop = threading.Event()
        self._broker = None
        self._port = None

        if mqtt:
            self.client = mqtt.Client(client_id=device_id, protocol=mqtt.MQTTv311)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
        else:
            self.client = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print(f"[SIM] {self.device_id} connected")
            self._publish_status("online")
        else:
            print(f"[SIM] {self.device_id} connection failed: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _ts(self) -> int:
        return int(time.time() * 1000)

    def _publish(self, sensor: str, value, unit: str, quality: int = 1):
        if self.client is None:
            return
        self.seq += 1
        payload = {
            "device_id": self.device_id,
            "org_id": _args.org,
            "site_id": _args.site,
            "sensor": sensor,
            "value": value,
            "unit": unit,
            "quality": quality,
            "ts": self._ts(),
            "seq": self.seq,
            "fw_version": "sim-1.0.0",
        }
        topic = f"iot/{_args.org}/{_args.site}/{self.device_id}/{sensor}/raw"
        self.client.publish(topic, json.dumps(payload), qos=0)
        if _args.verbose:
            print(f"  {topic}  {sensor}={value} {unit}")

    def _publish_status(self, status: str):
        if self.client is None:
            return
        payload = {
            "device_id": self.device_id,
            "status": status,
            "rssi": random.randint(-80, -40),
            "heap_free": random.randint(100000, 200000),
            "uptime_s": int(time.time() - self.start_time),
            "ts": self._ts(),
            "fw_version": "sim-1.0.0",
        }
        topic = f"iot/{_args.org}/{_args.site}/{self.device_id}/status"
        self.client.publish(topic, json.dumps(payload), qos=1, retain=True)

    def run(self):
        if self.client is None:
            return
        self.client.connect(_args.broker, _args.port, keepalive=60)
        self.client.loop_start()
        anomaly_triggered = False
        heartbeat_interval = int(60 / _args.interval)

        while not self._stop.is_set():
            loop_start = time.time()
            self.seq += 1
            self.model.tick()

            elapsed = time.time() - self.start_time
            if self.inject_anomaly and not anomaly_triggered and elapsed > 30:
                self.model.trigger_anomaly()
                anomaly_triggered = True

            self._publish("temperature",   self.model.temperature(),   "celsius")
            self._publish("humidity",      self.model.humidity(),      "percent_rh")
            self._publish("vibration_rms", self.model.vibration_rms(), "g")
            self._publish("vibration_peak", self.model.vibration_peak(), "g")
            self._publish("motor_current", self.model.motor_current(),  "amps")

            if (self.seq % heartbeat_interval) == 0:
                self._publish_status("online")

            elapsed = time.time() - loop_start
            time.sleep(max(0, _args.interval - elapsed))

        self._publish_status("offline")
        self.client.loop_stop()
        self.client.disconnect()

    def stop(self):
        self._stop.set()


_args = None


def main():
    global _args

    parser = argparse.ArgumentParser(description="IoT Device Simulator")
    parser.add_argument("--devices",  type=int,   default=3,    help="Number of simulated devices")
    parser.add_argument("--interval", type=float, default=5.0,  help="Reading interval in seconds")
    parser.add_argument("--broker",   default="localhost",      help="MQTT broker hostname")
    parser.add_argument("--port",     type=int,   default=1883,  help="MQTT broker port")
    parser.add_argument("--org",      default="demo",           help="Organisation ID")
    parser.add_argument("--site",     default="blr-demo",       help="Site ID")
    parser.add_argument("--anomaly",  action="store_true",      help="Enable anomaly injection on dev-0")
    parser.add_argument("--verbose",  action="store_true",      help="Print each published message")
    _args = parser.parse_args()

    stop_event = threading.Event()
    signal.signal(signal.SIGINT,  lambda s, f: stop_event.set())
    signal.signal(signal.SIGTERM, lambda s, f: stop_event.set())

    banner = (
        f"\n"
        f"  IoT Forge Device Simulator\n"
        f"  devices={_args.devices}  interval={_args.interval}s\n"
        f"  broker={_args.broker}:{_args.port}\n"
        f"  org={_args.org}  site={_args.site}\n"
        f"  anomaly={'ON' if _args.anomaly else 'off'}\n"
    )
    print(banner)

    if mqtt is None:
        print("[SIM] WARNING: paho-mqtt not installed. MQTT publishing disabled.")
        print("[SIM] Run: pip install paho-mqtt==2.1.0")

    time.sleep(0.5)

    devices = []
    for i in range(_args.devices):
        device_id = f"SIM-DEVICE-{i:04d}"
        inject = _args.anomaly and i == 0
        dev = SimDevice(device_id, seed=i, inject_anomaly=inject)
        devices.append(dev)
        print(f"[SIM] Starting device {i+1}/{_args.devices}: {device_id}")
        time.sleep(min(0.05, 5.0 / _args.devices))
        dev.start()

    print(f"[SIM] all {_args.devices} device(s) running. Press Ctrl+C to stop.")

    try:
        last_stats = time.time()
        while not stop_event.wait(timeout=1):
            now = time.time()
            elapsed = now - devices[0].start_time if devices else 0
            if now - last_stats >= 5:
                rate = _args.devices * 5 / _args.interval
                print(f"[SIM] t={elapsed:.0f}s  devices={_args.devices}  approx_msgs/s={rate:.0f}")
                last_stats = now
    finally:
        for dev in devices:
            dev.stop()
        for dev in devices:
            dev.join(timeout=3)
        print("[SIM] all devices stopped.")


if __name__ == "__main__":
    main()