# ============================================================
# DHT22 Driver - Temperature and Humidity sensor
# Returns list with TWO readings: temperature + humidity
# Must handle hardware exceptions and return quality=0, not raise
# ============================================================

import dht
import machine


class DHT22Driver:
    def __init__(self, pin_config):
        self.pin = machine.Pin(pin_config.get("data_pin", 4))
        self.sensor = dht.DHT22(self.pin)

    def read(self):
        readings = []
        try:
            self.sensor.measure()
            temperature = self.sensor.temperature()
            humidity = self.sensor.humidity()

            if temperature is not None:
                readings.append({
                    "sensor": "temperature",
                    "value": temperature,
                    "unit": "celsius",
                    "quality": 1
                })
            else:
                readings.append({
                    "sensor": "temperature",
                    "value": 0,
                    "unit": "celsius",
                    "quality": 0
                })

            if humidity is not None:
                readings.append({
                    "sensor": "humidity",
                    "value": humidity,
                    "unit": "percent",
                    "quality": 1
                })
            else:
                readings.append({
                    "sensor": "humidity",
                    "value": 0,
                    "unit": "percent",
                    "quality": 0
                })

        except Exception as e:
            print(f"[DHT22] read error: {e}")
            readings.append({
                "sensor": "temperature",
                "value": 0,
                "unit": "celsius",
                "quality": 0
            })
            readings.append({
                "sensor": "humidity",
                "value": 0,
                "unit": "percent",
                "quality": 0
            })

        return readings