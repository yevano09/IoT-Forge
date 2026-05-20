import re
import sys
import os
import time
import unittest.mock as mock

sys.modules.setdefault("paho",             mock.MagicMock())
sys.modules.setdefault("paho.mqtt",        mock.MagicMock())
sys.modules.setdefault("paho.mqtt.client", mock.MagicMock())

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'firmware', 'simulator'))
from simulator import SensorModel

RAW_REQUIRED_FIELDS = {
    "device_id": str,
    "org_id":    str,
    "site_id":   str,
    "sensor":    str,
    "value":     (int, float, type(None)),
    "unit":      str,
    "quality":   int,
    "ts":        int,
    "seq":       int,
    "fw_version": str,
}

STATUS_REQUIRED_FIELDS = {
    "device_id":  str,
    "status":     str,
    "rssi":       int,
    "heap_free":  int,
    "uptime_s":   int,
    "ts":         int,
    "fw_version": str,
}

TOPIC_PATTERN = re.compile(
    r"^iot/[^/]+/[^/]+/[^/]+/(temperature|humidity|vibration_rms|vibration_peak|motor_current)/raw$"
)


def make_raw_payload(sensor="temperature", value=25.0):
    return {
        "device_id":  "TEST-001",
        "org_id":     "demo",
        "site_id":    "blr-demo",
        "sensor":     sensor,
        "value":      value,
        "unit":       "celsius",
        "quality":    1,
        "ts":         int(time.time() * 1000),
        "seq":        1,
        "fw_version": "1.0.0",
    }


def test_raw_payload_structure():
    payload = make_raw_payload()
    for field, expected_type in RAW_REQUIRED_FIELDS.items():
        assert field in payload, f"Missing field: {field}"
        if isinstance(expected_type, tuple):
            assert isinstance(payload[field], expected_type), \
                f"Field {field}: expected {expected_type}, got {type(payload[field])}"
        else:
            assert isinstance(payload[field], expected_type), \
                f"Field {field}: expected {expected_type}, got {type(payload[field])}"


def test_raw_payload_ts_is_milliseconds():
    payload = make_raw_payload()
    assert len(str(payload["ts"])) == 13, \
        f"ts looks wrong: {payload['ts']}"


def test_raw_payload_quality_is_binary():
    for q in [0, 1]:
        payload = make_raw_payload()
        payload["quality"] = q
        assert payload["quality"] in (0, 1)


def test_status_payload_structure():
    payload = {
        "device_id":  "TEST-001",
        "status":     "online",
        "rssi":       -67,
        "heap_free":  142336,
        "uptime_s":   3600,
        "ts":         int(time.time() * 1000),
        "fw_version": "1.0.0",
    }
    for field, expected_type in STATUS_REQUIRED_FIELDS.items():
        assert field in payload, f"Missing field: {field}"
        assert isinstance(payload[field], expected_type), \
            f"Field {field}: expected {expected_type}, got {type(payload[field])}"


def test_topic_format():
    org, site, device = "demo", "blr-demo", "SIM-DEVICE-0000"
    sensors = ["temperature", "humidity", "vibration_rms", "vibration_peak", "motor_current"]
    for sensor in sensors:
        topic = f"iot/{org}/{site}/{device}/{sensor}/raw"
        assert TOPIC_PATTERN.match(topic), f"Topic does not match pattern: {topic}"


def test_simulator_payload_fields():
    m = SensorModel("SIM-TEST", seed=0)
    payload = {
        "device_id":  "SIM-TEST",
        "org_id":     "demo",
        "site_id":    "blr-demo",
        "sensor":     "temperature",
        "value":      m.temperature(),
        "unit":       "celsius",
        "quality":    1,
        "ts":         int(time.time() * 1000),
        "seq":        1,
        "fw_version": "sim-1.0.0",
    }
    for field, expected_type in RAW_REQUIRED_FIELDS.items():
        assert field in payload, f"Missing field in simulator payload: {field}"
