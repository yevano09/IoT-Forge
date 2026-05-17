# ============================================================
# Test MQTT Schema - Validate topic patterns and payloads
# ============================================================

import pytest
import json
import re


class TestMQTTSchema:
    def test_topic_pattern_raw_reading(self):
        pattern = r"iot/[^/]+/[^/]+/[^/]+/[^/]+/raw"
        valid_topics = [
            "iot/acme/blr-plant-1/ESP32-A1B2C3/temperature/raw",
            "iot/acme/test-site/device-123/vibration/raw",
        ]
        invalid_topics = [
            "iot/acme/blr-plant-1/ESP32/temperature",
            "invalid/topic",
        ]

        for topic in valid_topics:
            assert re.match(pattern, topic), f"Valid topic {topic} should match"

        for topic in invalid_topics:
            assert not re.match(pattern, topic), f"Invalid topic {topic} should not match"

    def test_topic_pattern_status(self):
        pattern = r"iot/[^/]+/[^/]+/[^/]+/status"
        valid_topics = [
            "iot/acme/blr-plant-1/ESP32-A1B2C3/status",
        ]
        invalid_topics = [
            "iot/acme/blr-plant-1/status",
        ]

        for topic in valid_topics:
            assert re.match(pattern, topic), f"Valid topic {topic} should match"

    def test_raw_reading_payload_schema(self):
        payload = {
            "device_id": "ESP32-A1B2C3",
            "org_id": "acme",
            "site_id": "blr-plant-1",
            "sensor": "temperature",
            "value": 42.7,
            "unit": "celsius",
            "quality": 1,
            "ts": 1716000000000,
            "seq": 1042,
            "fw_version": "1.0.3"
        }

        required_fields = [
            "device_id", "org_id", "site_id", "sensor",
            "value", "unit", "quality", "ts", "seq"
        ]

        for field in required_fields:
            assert field in payload, f"Required field {field} missing"

        assert isinstance(payload["value"], (int, float))
        assert isinstance(payload["ts"], int)
        assert payload["quality"] in [0, 1]

    def test_status_payload_schema(self):
        payload = {
            "device_id": "ESP32-A1B2C3",
            "status": "online",
            "rssi": -67,
            "heap_free": 142336,
            "uptime_s": 86400,
            "ts": 1716000000000,
            "fw_version": "1.0.3"
        }

        required_fields = ["device_id", "status", "ts"]
        for field in required_fields:
            assert field in payload, f"Required field {field} missing"

        assert payload["status"] in ["online", "offline"]
        assert isinstance(payload["ts"], int)

    def test_qos_levels(self):
        qos_mapping = {
            "raw": 0,
            "status": 1,
            "cmd": 1,
            "cmd/ack": 1
        }

        for topic_suffix, expected_qos in qos_mapping.items():
            assert expected_qos in [0, 1, 2]


class TestPayloadValidation:
    def test_valid_temperature_reading(self):
        payload = {
            "device_id": "test-device",
            "org_id": "acme",
            "site_id": "test-site",
            "sensor": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "quality": 1,
            "ts": 1716000000000,
            "seq": 1,
            "fw_version": "1.0.0"
        }

        data = json.dumps(payload)
        parsed = json.loads(data)
        assert parsed["sensor"] == "temperature"
        assert parsed["value"] > -50 and parsed["value"] < 100

    def test_invalid_payload_missing_fields(self):
        payload = {
            "device_id": "test-device",
            "value": 25.5
        }

        required = ["device_id", "org_id", "site_id", "sensor", "value", "ts"]
        for field in required:
            assert field in payload, f"Payload missing required field: {field}"

    def test_quality_zero_on_error(self):
        payload = {
            "device_id": "test-device",
            "org_id": "acme",
            "site_id": "test-site",
            "sensor": "temperature",
            "value": 0,
            "unit": "celsius",
            "quality": 0,
            "ts": 1716000000000,
            "seq": 1,
            "fw_version": "1.0.0"
        }

        assert payload["quality"] == 0
        assert payload["value"] == 0