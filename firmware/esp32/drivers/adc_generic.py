# ============================================================
# Generic ADC Driver with oversampling, scale, and offset
# ============================================================

import machine
import utime


class ADCGenericDriver:
    def __init__(self, pin_config, options=None):
        self.adc_pin = machine.Pin(pin_config.get("adc_pin", 34))
        self.adc = machine.ADC(self.adc_pin)
        self.adc.atten(machine.ADC.ATTN_11DB)

        self.mode = (options or {}).get("mode", "voltage")
        self.sensor_name = (options or {}).get("sensor_name", "adc")
        self.scale = (options or {}).get("scale", 1.0)
        self.offset = (options or {}).get("offset", 0.0)
        self.samples = (options or {}).get("samples", 32)
        self.unit = (options or {}).get("unit", "volts")

    def read(self):
        readings = []
        try:
            values = []
            for _ in range(self.samples):
                raw = self.adc.read()
                voltage = (raw / 4095.0) * 3.3
                values.append(voltage)
                utime.sleep_ms(1)

            if values:
                avg_raw = sum(values) / len(values)
                scaled_value = (avg_raw * self.scale) + self.offset

                readings.append({
                    "sensor": self.sensor_name,
                    "value": round(scaled_value, 4),
                    "unit": self.unit,
                    "quality": 1
                })
            else:
                readings.append({
                    "sensor": self.sensor_name,
                    "value": 0,
                    "unit": self.unit,
                    "quality": 0
                })

        except Exception as e:
            print(f"[ADC] read error: {e}")
            readings.append({
                "sensor": self.sensor_name,
                "value": 0,
                "unit": self.unit,
                "quality": 0
            })

        return readings