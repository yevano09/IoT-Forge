# ============================================================
# DHT22 Driver - Temperature and Humidity sensor
# ============================================================
#
# Wiring:
#   - VCC -> 3.3V, GND -> GND, DATA -> data_pin
#   - 10kOhm pull-up resistor between DATA and VCC required
#   - Minimum 2s between reads (DHT22 hardware limitation)
#
# Interface:
#   class Driver:
#     def __init__(self, pin_config: dict, options: dict): ...
#     def read(self) -> list: ...
# ============================================================

import dht
import machine


class Driver:
    def __init__(self, pin_config: dict, options: dict):
        self._pin = machine.Pin(pin_config.get("data_pin", 4))
        self._sensor = dht.DHT22(self._pin)
        self._last_temp = None
        self._last_hum = None

    def read(self) -> list:
        temp_ok = False
        hum_ok = False

        try:
            self._sensor.measure()
            temperature = self._sensor.temperature()
            humidity = self._sensor.humidity()

            if -40.0 <= temperature <= 80.0:
                temp_ok = True
                self._last_temp = temperature
            else:
                print(f"[DHT22] temperature out of range: {temperature}")
                self._last_temp = temperature

            if 0.0 <= humidity <= 100.0:
                hum_ok = True
                self._last_hum = humidity
            else:
                print(f"[DHT22] humidity out of range: {humidity}")
                self._last_hum = humidity

        except Exception as e:
            print(f"[DHT22] read error: {e}")

        if temp_ok:
            temp_value = self._last_temp
            temp_quality = 1
        else:
            temp_value = self._last_temp
            temp_quality = 0

        if hum_ok:
            hum_value = self._last_hum
            hum_quality = 1
        else:
            hum_value = self._last_hum
            hum_quality = 0

        return [
            {"sensor": "temperature", "value": temp_value, "unit": "celsius",    "quality": temp_quality},
            {"sensor": "humidity",    "value": hum_value,  "unit": "percent_rh", "quality": hum_quality},
        ]