# ============================================================
# Test Sensor Drivers - Mock MicroPython hardware modules
# ============================================================

import sys
import os
from unittest.mock import MagicMock

machine_mock = MagicMock()
machine_mock.Pin = MagicMock()
machine_mock.I2C = MagicMock()
machine_mock.ADC = MagicMock()
machine_mock.ADC.ATTN_11DB = 3

dht_mock = MagicMock()
utime_mock = MagicMock()
utime_mock.sleep_ms = MagicMock()

sys.modules["machine"] = machine_mock
sys.modules["dht"] = dht_mock
sys.modules["utime"] = utime_mock
sys.modules["math"] = __import__("math")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware", "esp32"))

import importlib.util

def load_driver(name):
    spec = importlib.util.spec_from_file_location(f"drivers.{name}", f"C:\\code\\IoT-Forge\\month1-edge-sense\\firmware\\esp32\\drivers\\{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"drivers.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod

import pytest


class TestDHT22:
    def test_returns_two_readings(self):
        dht22_mod = load_driver("dht22")
        mock_sensor = MagicMock()
        mock_sensor.temperature.return_value = 25.0
        mock_sensor.humidity.return_value = 60.0
        dht_mock.DHT22.return_value = mock_sensor

        driver = dht22_mod.Driver({"data_pin": 4}, {})
        result = driver.read()

        assert len(result) == 2
        assert result[0]["sensor"] == "temperature"
        assert result[1]["sensor"] == "humidity"
        assert result[0]["quality"] == 1
        assert result[1]["quality"] == 1

    def test_quality_flag_on_out_of_range(self):
        dht22_mod = load_driver("dht22")
        mock_sensor = MagicMock()
        mock_sensor.temperature.return_value = 100.0
        mock_sensor.humidity.return_value = 50.0
        dht_mock.DHT22.return_value = mock_sensor

        driver = dht22_mod.Driver({"data_pin": 4}, {})
        result = driver.read()

        assert result[0]["quality"] == 0
        assert result[0]["value"] == 100.0


class TestMPU6050:
    def test_returns_rms_and_peak(self):
        mpu6050_mod = load_driver("mpu6050")
        i2c_mock = MagicMock()
        machine_mock.I2C.return_value = i2c_mock
        i2c_mock.readfrom_mem.return_value = bytes([0x10, 0x00, 0x10, 0x00, 0x40, 0x00])

        driver = mpu6050_mod.Driver({"sda_pin": 21, "scl_pin": 22}, {"samples": 3})
        result = driver.read()

        assert len(result) == 2
        assert result[0]["sensor"] == "vibration_rms"
        assert result[1]["sensor"] == "vibration_peak"
        assert result[0]["value"] is not None
        assert result[0]["quality"] == 1


class TestADCGeneric:
    def test_conversion(self):
        adc_mod = load_driver("adc_generic")
        mock_adc = MagicMock()
        mock_adc.read.return_value = 2048
        machine_mock.ADC.return_value = mock_adc

        driver = adc_mod.Driver(
            {"adc_pin": 34},
            {"mode": "voltage", "scale": 2.0, "offset": 0.0, "v_ref": 3.3, "adc_bits": 12, "samples": 1}
        )
        result = driver.read()

        expected_voltage = (2048 / 4095) * 3.3
        expected_value = expected_voltage * 2.0 + 0.0
        assert abs(result[0]["value"] - expected_value) < 0.05
        assert result[0]["quality"] == 1