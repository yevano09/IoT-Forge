# ============================================================
# Test Simulator - Verify simulator output and anomaly injection
# ============================================================

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock


class TestSimulatorPayloads:
    def test_payload_has_required_fields(self):
        payload = {
            "device_id": "test-device",
            "org_id": "acme",
            "site_id": "test-site",
            "sensor": "temperature",
            "value": 25.0,
            "unit": "celsius",
            "quality": 1,
            "ts": int(time.time() * 1000),
            "seq": 1,
            "fw_version": "1.0.0-sim"
        }

        required = ["device_id", "org_id", "site_id", "sensor", "value", "unit", "quality", "ts", "seq", "fw_version"]
        for field in required:
            assert field in payload, f"Missing field: {field}"

    def test_temperature_range_valid(self):
        from firmware.simulator.simulator import DeviceSimulator

        with patch('paho.mqtt.client.Client') as mock_client:
            mock_client.return_value.connect.return_value = 0
            mock_client.return_value.publish.return_value = Mock(rc=0)

            sim = DeviceSimulator(
                org_id="acme",
                site_id="test-site",
                device_id="test-device",
                mqtt_broker="localhost",
                mqtt_port=1883,
                interval=1
            )

            temperature = sim._generate_temperature()
            assert -20 <= temperature <= 60

    def test_humidity_range_valid(self):
        from firmware.simulator.simulator import DeviceSimulator

        with patch('paho.mqtt.client.Client') as mock_client:
            mock_client.return_value.connect.return_value = 0
            mock_client.return_value.publish.return_value = Mock(rc=0)

            sim = DeviceSimulator(
                org_id="acme",
                site_id="test-site",
                device_id="test-device",
                mqtt_broker="localhost",
                mqtt_port=1883,
                interval=1
            )

            humidity = sim._generate_humidity()
            assert 0 <= humidity <= 100

    def test_vibration_normal_range(self):
        from firmware.simulator.simulator import DeviceSimulator

        with patch('paho.mqtt.client.Client') as mock_client:
            mock_client.return_value.connect.return_value = 0
            mock_client.return_value.publish.return_value = Mock(rc=0)

            sim = DeviceSimulator(
                org_id="acme",
                site_id="test-site",
                device_id="test-device",
                mqtt_broker="localhost",
                mqtt_port=1883,
                interval=1
            )

            sim.start_time = time.time() - 10
            vibration = sim._generate_vibration()

            assert "vibration_rms" in vibration
            assert "vibration_peak" in vibration
            assert vibration["vibration_rms"] < 0.30

    def test_vibration_anomaly_exceeds_threshold(self):
        from firmware.simulator.simulator import DeviceSimulator

        with patch('paho.mqtt.client.Client') as mock_client:
            mock_client.return_value.connect.return_value = 0
            mock_client.return_value.publish.return_value = Mock(rc=0)

            sim = DeviceSimulator(
                org_id="acme",
                site_id="test-site",
                device_id="test-device",
                mqtt_broker="localhost",
                mqtt_port=1883,
                interval=1
            )

            sim.start_time = time.time() - 35
            sim.anomaly_triggered = True

            vibration = sim._generate_vibration()

            assert vibration["vibration_rms"] > 0.30, f"Expected >0.30, got {vibration['vibration_rms']}"


class TestSimulatorMQTTIntegration:
    @patch('paho.mqtt.client.Client')
    def test_publish_success(self, mock_client):
        from firmware.simulator.simulator import DeviceSimulator

        mock_instance = Mock()
        mock_instance.connect.return_value = 0
        mock_instance.publish.return_value = Mock(rc=0)
        mock_client.return_value = mock_instance

        sim = DeviceSimulator(
            org_id="acme",
            site_id="test-site",
            device_id="test-device",
            mqtt_broker="localhost",
            mqtt_port=1883,
            interval=1
        )

        sim._publish_reading("temperature", 25.0, "celsius")

        mock_instance.publish.assert_called_once()

    @patch('paho.mqtt.client.Client')
    def test_status_publish(self, mock_client):
        from firmware.simulator.simulator import DeviceSimulator

        mock_instance = Mock()
        mock_instance.connect.return_value = 0
        mock_instance.publish.return_value = Mock(rc=0)
        mock_client.return_value = mock_instance

        sim = DeviceSimulator(
            org_id="acme",
            site_id="test-site",
            device_id="test-device",
            mqtt_broker="localhost",
            mqtt_port=1883,
            interval=1
        )

        sim._publish_status()

        assert mock_instance.publish.call_count >= 1


class TestSimulatorMultipleDevices:
    def test_multiple_devices_have_unique_ids(self):
        from firmware.simulator.simulator import DeviceSimulator

        with patch('paho.mqtt.client.Client') as mock_client:
            mock_client.return_value.connect.return_value = 0
            mock_client.return_value.publish.return_value = Mock(rc=0)

            device_ids = set()
            for i in range(5):
                sim = DeviceSimulator(
                    org_id="acme",
                    site_id="test-site",
                    device_id=f"ESP32-{i}",
                    mqtt_broker="localhost",
                    mqtt_port=1883,
                    interval=1
                )
                device_ids.add(sim.device_id)

            assert len(device_ids) == 5