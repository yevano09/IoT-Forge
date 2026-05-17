# ============================================================
# SensorRegistry - Dynamic driver loader using importlib
# Never crashes on bad driver
# ============================================================

import sys


class SensorRegistry:
    def __init__(self, sensor_configs):
        self.sensors = []
        self._load_sensors(sensor_configs)

    def _load_sensors(self, sensor_configs):
        for config in sensor_configs:
            driver_name = config.get("driver")
            sensor_type = config.get("sensor_type")
            pin_config = config.get("pin_config", {})
            options = config.get("options", {})

            try:
                module_name = f"drivers.{driver_name}"
                if module_name in sys.modules:
                    driver_module = sys.modules[module_name]
                else:
                    __import__(module_name)

                driver_class = None
                if driver_name == "dht22":
                    from drivers.dht22 import DHT22Driver
                    driver_class = DHT22Driver
                elif driver_name == "mpu6050":
                    from drivers.mpu6050 import MPU6050Driver
                    driver_class = MPU6050Driver
                elif driver_name == "adc_generic":
                    from drivers.adc_generic import ADCGenericDriver
                    driver_class = ADCGenericDriver

                if driver_class:
                    driver_instance = driver_class(pin_config, options)
                    self.sensors.append({
                        "driver": driver_instance,
                        "sensor_type": sensor_type,
                        "unit": config.get("unit", "")
                    })
                    print(f"[REGISTRY] loaded driver: {driver_name} for {sensor_type}")
                else:
                    print(f"[REGISTRY] no class found for driver: {driver_name}")

            except Exception as e:
                print(f"[REGISTRY] failed to load {driver_name}: {e}")
                continue

    def read_all(self):
        all_readings = []
        for sensor in self.sensors:
            try:
                readings = sensor["driver"].read()
                if readings:
                    for reading in readings:
                        reading["sensor_type"] = sensor.get("sensor_type", reading.get("sensor"))
                        all_readings.append(reading)
            except Exception as e:
                print(f"[REGISTRY] error reading {sensor.get('sensor_type')}: {e}")
                continue
        return all_readings