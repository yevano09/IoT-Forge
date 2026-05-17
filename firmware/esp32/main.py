# ============================================================
# IoT Forge — Edge Sense Firmware v1.0
# Target: ESP32 (MicroPython 1.23+)
# File: main.py
# ============================================================
# Architecture:
#   config.json  →  SensorDriver (pluggable)
#                →  LocalBuffer (SQLite)
#                →  MQTTClient  (TLS + auto-retry)
#                →  StatusReporter (heartbeat)
#
# Adding a new sensor: create a file in /drivers/ and add
# its name to config.json. Zero changes to this file.
# ============================================================

import ujson
import utime
import machine
import ubinascii
import uos
import gc

from mqtt_client import MQTTClient
from local_buffer import LocalBuffer
from sensor_registry import SensorRegistry
from status_reporter import StatusReporter


def load_config():
    try:
        if "config.json" in uos.listdir():
            with open("config.json") as f:
                return ujson.load(f)
    except Exception:
        pass
    return {}


cfg = load_config()

DEVICE_ID = cfg.get("device_id") or ubinascii.hexlify(machine.unique_id()).decode()
ORG_ID = cfg.get("org_id", "acme")
SITE_ID = cfg.get("site_id", "default-site")
FW_VERSION = cfg.get("fw_version", "1.0.0")

TOPIC_BASE = f"iot/{ORG_ID}/{SITE_ID}/{DEVICE_ID}"
TOPIC_STATUS = f"{TOPIC_BASE}/status"
TOPIC_CMD = f"{TOPIC_BASE}/cmd/#"

INTERVAL_MS = cfg.get("interval_ms", 5000)
HEARTBEAT_S = cfg.get("heartbeat_s", 60)

buffer = LocalBuffer(max_records=500)
registry = SensorRegistry(cfg.get("sensors", []))
client = MQTTClient(cfg.get("mqtt", {}), DEVICE_ID)
reporter = StatusReporter(client, TOPIC_STATUS, DEVICE_ID, FW_VERSION)

seq = 0
last_heartbeat = 0


def on_command(topic, payload):
    try:
        cmd = ujson.loads(payload)
        global INTERVAL_MS
        if cmd.get("cmd") == "set_interval":
            INTERVAL_MS = cmd.get("params", {}).get("interval_ms", 5000)
            print(f"[CMD] interval_ms → {INTERVAL_MS}")
        elif cmd.get("cmd") == "reboot":
            machine.reset()
        topic_str = topic.decode() if isinstance(topic, bytes) else topic
        ack_topic = topic_str.replace("/cmd/", "/cmd/") + "/ack"
        client.publish(ack_topic, ujson.dumps({
            "cmd_id": cmd.get("cmd_id"),
            "status": "ok",
            "device_id": DEVICE_ID
        }), qos=1)
    except Exception as e:
        print(f"[CMD ERR] {e}")


def connect_wifi():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("[WIFI] connecting...")
        wifi_config = cfg.get("wifi", {})
        wlan.connect(wifi_config.get("ssid", ""), wifi_config.get("password", ""))
        deadline = utime.ticks_ms() + 15000
        while not wlan.isconnected():
            if utime.ticks_diff(utime.ticks_ms(), deadline) > 0:
                print("[WIFI] timeout — running offline")
                return False
            utime.sleep_ms(200)
    print(f"[WIFI] connected  ip={wlan.ifconfig()[0]}")
    return True


def flush_buffer():
    records = buffer.get_all()
    if not records:
        return
    print(f"[BUF] flushing {len(records)} buffered readings")
    for rec in records:
        topic = f"{TOPIC_BASE}/{rec.get('sensor', 'unknown')}/raw"
        client.publish(topic, ujson.dumps(rec), qos=0)
    buffer.clear()


def main():
    global seq, last_heartbeat

    online = connect_wifi()
    if online:
        client.connect(on_command, [TOPIC_CMD])
        flush_buffer()

    while True:
        loop_start = utime.ticks_ms()

        readings = registry.read_all()
        seq += 1

        for reading in readings:
            sensor_type = reading.get("sensor_type", reading.get("sensor", "unknown"))
            payload = {
                "device_id": DEVICE_ID,
                "org_id": ORG_ID,
                "site_id": SITE_ID,
                "sensor": sensor_type,
                "value": reading.get("value", 0),
                "unit": reading.get("unit", ""),
                "quality": reading.get("quality", 1),
                "ts": utime.time() * 1000,
                "seq": seq,
                "fw_version": FW_VERSION
            }
            topic = f"{TOPIC_BASE}/{sensor_type}/raw"

            if client.is_connected():
                result = client.publish(topic, ujson.dumps(payload), qos=0)
                if result:
                    print(f"[PUB] {topic}  val={reading.get('value')}")
                else:
                    buffer.add(payload)
                    print(f"[BUF] offline — buffered  sensor={sensor_type}")
            else:
                buffer.add(payload)
                print(f"[BUF] offline — buffered  sensor={sensor_type}")

        now = utime.time()
        if now - last_heartbeat >= HEARTBEAT_S:
            if client.is_connected():
                reporter.send()
            last_heartbeat = now

        if not client.is_connected():
            client.reconnect()
            if client.is_connected():
                flush_buffer()

        elapsed = utime.ticks_diff(utime.ticks_ms(), loop_start)
        sleep_ms = max(0, INTERVAL_MS - elapsed)
        utime.sleep_ms(sleep_ms)
        gc.collect()


if __name__ == "__main__":
    main()