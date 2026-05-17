# ============================================================
# Test Sensor Drivers - Mock hardware modules
# ============================================================

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestDHT22Driver:
    @patch('drivers.dht22.dht')
    @patch('drivers.dht22.machine.Pin')
    def test_read_returns_two_readings(self, mock_pin, mock_dht):
        mock_sensor = Mock()
        mock_sensor.temperature.return_value = 25.5
        mock_sensor.humidity.return_value = 60.0
        mock_dht.DHT22.return_value = mock_sensor

        from drivers.dht22 import DHT22Driver
        driver = DHT22Driver({"data_pin": 4})
        readings = driver.read()

        assert len(readings) == 2
        assert readings[0]["sensor"] == "temperature"
        assert readings[1]["sensor"] == "humidity"

    @patch('drivers.dht22.dht')
    @patch('drivers.dht22.machine.Pin')
    def test_read_handles_exception(self, mock_pin, mock_dht):
        mock_sensor = Mock()
        mock_sensor.measure.side_effect = Exception("Hardware error")
        mock_dht.DHT22.return_value = mock_sensor

        from drivers.dht22 import DHT22Driver
        driver = DHT22Driver({"data_pin": 4})
        readings = driver.read()

        assert len(readings) == 2
        assert readings[0]["quality"] == 0
        assert readings[1]["quality"] == 0


class TestMPU6050Driver:
    @patch('drivers.mpu6050.machine')
    def test_read_returns_vibration_readings(self, mock_machine):
        mock_i2c = Mock()
        mock_i2c.readfrom_mem.return_value = b'\x00\x00\x00\x00\x00\x00'
        mock_machine.SoftI2C.return_value = mock_i2c

        import sys
        sys.modules['ustruct'] = __import__('struct')
        sys.modules['utime'] = __import__('time')

        with patch('drivers.mpu6050.machine.SoftI2C', return_value=mock_i2c):
            from drivers.mpu6050 import MPU6050Driver
            driver = MPU6050Driver({"sda_pin": 21, "scl_pin": 22}, {"samples": 3})
            readings = driver.read()

            assert len(readings) == 2
            assert readings[0]["sensor_type"] == "vibration_rms"
            assert readings[1]["sensor_type"] == "vibration_peak"

    @patch('drivers.mpu6050.machine')
    def test_read_subtracts_gravity(self, mock_machine):
        import struct
        import sys
        sys.modules['struct'] = struct

        mock_i2c = Mock()
        mock_i2c.readfrom_mem.return_value = struct.pack(">hhh", 0, 0, 32768)
        mock_machine.SoftI2C.return_value = mock_i2c

        with patch('drivers.mpu6050.machine.SoftI2C', return_value=mock_i2c):
            from drivers.mpu6050 import MPU6050Driver
            driver = MPU6050Driver({"sda_pin": 21, "scl_pin": 22}, {"samples": 1})
            readings = driver.read()

            assert readings[0]["value"] >= 0


class TestADCGenericDriver:
    @patch('drivers.adc_generic.machine')
    def test_read_returns_scaled_value(self, mock_machine):
        mock_adc = Mock()
        mock_adc.read.return_value = 2048
        mock_machine.ADC.return_value = mock_adc

        with patch('drivers.adc_generic.machine.ADC', return_value=mock_adc):
            from drivers.adc_generic import ADCGenericDriver
            driver = ADCGenericDriver(
                {"adc_pin": 34},
                {"scale": 2.0, "offset": 1.0, "samples": 1}
            )
            readings = driver.read()

            assert len(readings) == 1
            assert "value" in readings[0]
            assert readings[0]["quality"] == 1

    @patch('drivers.adc_generic.machine')
    def test_read_handles_exception(self, mock_machine):
        mock_adc = Mock()
        mock_adc.read.side_effect = Exception("ADC error")
        mock_machine.ADC.return_value = mock_adc

        with patch('drivers.adc_generic.machine.ADC', return_value=mock_adc):
            from drivers.adc_generic import ADCGenericDriver
            driver = ADCGenericDriver({"adc_pin": 34}, {})
            readings = driver.read()

            assert readings[0]["quality"] == 0


class TestSensorRegistry:
    @patch('drivers.dht22.DHT22Driver')
    def test_load_sensors_from_config(self, mock_driver_class):
        mock_driver = Mock()
        mock_driver.read.return_value = [
            {"sensor": "temperature", "value": 25.0, "unit": "celsius", "quality": 1}
        ]
        mock_driver_class.return_value = mock_driver

        from sensor_registry import SensorRegistry

        config = [
            {
                "driver": "dht22",
                "sensor_type": "temperature",
                "unit": "celsius",
                "pin_config": {"data_pin": 4}
            }
        ]

        registry = SensorRegistry(config)
        assert len(registry.sensors) == 1

    @patch('drivers.dht22.DHT22Driver')
    def test_read_all_returns_combined_readings(self, mock_driver_class):
        mock_driver = Mock()
        mock_driver.read.return_value = [
            {"sensor": "temperature", "value": 25.0, "unit": "celsius", "quality": 1}
        ]
        mock_driver_class.return_value = mock_driver

        from sensor_registry import SensorRegistry

        config = [
            {
                "driver": "dht22",
                "sensor_type": "temperature",
                "unit": "celsius",
                "pin_config": {"data_pin": 4}
            }
        ]

        registry = SensorRegistry(config)
        readings = registry.read_all()

        assert len(readings) > 0

    @patch('drivers.dht22.DHT22Driver')
    def test_never_crashes_on_bad_driver(self, mock_driver_class):
        mock_driver_class.side_effect = Exception("Driver load error")

        from sensor_registry import SensorRegistry

        config = [
            {
                "driver": "nonexistent",
                "sensor_type": "test",
                "pin_config": {}
            }
        ]

        registry = SensorRegistry(config)
        assert len(registry.sensors) == 0