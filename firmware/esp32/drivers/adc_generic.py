# ============================================================
# Generic ADC Driver with oversampling, scale, and offset
# ============================================================
#
# Wiring:
#   - Only use GPIO pins 32-39 for ADC on ESP32 (input-only pins)
#   - Do not use ADC2 pins (GPIO 0,2,4,12-15,25-27) -- conflicts with WiFi
#   - Max input voltage: 3.3V (with ATTN_11DB). Do NOT exceed 3.3V.
#   - For current sensing with ACS712: scale=66.0 (5A module), offset=-3.3*66/2
#
# Interface:
#   class Driver:
#     def __init__(self, pin_config: dict, options: dict): ...
#     def read(self) -> list: ...
# ============================================================

import machine


class Driver:
    def __init__(self, pin_config: dict, options: dict):
        pin_num = pin_config.get("adc_pin", 34)
        self._adc = machine.ADC(machine.Pin(pin_num))
        self._adc.atten(machine.ADC.ATTN_11DB)
        self._mode = options.get("mode", "voltage")
        self._v_ref = options.get("v_ref", 3.3)
        self._max_raw = (1 << options.get("adc_bits", 12)) - 1
        self._scale = options.get("scale", 1.0)
        self._offset = options.get("offset", 0.0)
        self._unit = options.get("unit", "volts")
        self._samples = options.get("samples", 16)
        self._sensor_name = options.get("sensor_name", "adc")

    def _oversample(self) -> float:
        total = 0
        for _ in range(self._samples):
            total += self._adc.read()
        return total / self._samples

    def read(self) -> list:
        try:
            raw = self._oversample()
            if self._mode == "raw":
                value = raw
            else:
                voltage = (raw / self._max_raw) * self._v_ref
                value = (voltage * self._scale) + self._offset
            value = round(value, 4)
            return [
                {"sensor": self._sensor_name, "value": value, "unit": self._unit, "quality": 1}
            ]
        except Exception as e:
            print(f"[ADC] read error: {e}")
            return [
                {"sensor": self._sensor_name, "value": None, "unit": self._unit, "quality": 0}
            ]