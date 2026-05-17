# ============================================================
# MPU-6050 I2C Driver
# Returns vibration_rms and vibration_peak in g
# Subtract gravity from Z axis before computing magnitude
# ============================================================

import machine
import ustruct
import math


class MPU6050Driver:
    def __init__(self, pin_config, options=None):
        self.sda_pin = pin_config.get("sda_pin", 21)
        self.scl_pin = pin_config.get("scl_pin", 22)
        self.samples = (options or {}).get("samples", 10)
        self.range_g = (options or {}).get("range_g", 2)

        self.i2c = machine.SoftI2C(scl=machine.Pin(self.scl_pin),
                                    sda=machine.Pin(self.sda_pin),
                                    freq=400000)

        self._init_sensor()

    def _init_sensor(self):
        try:
            self.i2c.start()
            self.i2c.writeto(0x68, bytearray([0x6B, 0]))
            self.i2c.stop()
        except Exception as e:
            print(f"[MPU6050] init error: {e}")

    def _read_raw(self):
        try:
            data = self.i2c.readfrom_mem(0x68, 0x3B, 6)
            ax, ay, az = ustruct.unpack(">hhh", data)
            return (ax / 16384.0, ay / 16384.0, az / 16384.0)
        except Exception:
            return (0, 0, 0)

    def read(self):
        readings = []
        samples = []

        for _ in range(self.samples):
            ax, ay, az = self._read_raw()
            az_corrected = az - 1.0
            magnitude = math.sqrt(ax * ax + ay * ay + az_corrected * az_corrected)
            samples.append(magnitude)
            utime.sleep_ms(5)

        import utime
        try:
            if samples:
                rms = math.sqrt(sum(s * s for s in samples) / len(samples))
                peak = max(samples)
            else:
                rms = 0.0
                peak = 0.0
        except Exception:
            rms = 0.0
            peak = 0.0

        readings.append({
            "sensor": "vibration",
            "sensor_type": "vibration_rms",
            "value": round(rms, 4),
            "unit": "g",
            "quality": 1
        })

        readings.append({
            "sensor": "vibration",
            "sensor_type": "vibration_peak",
            "value": round(peak, 4),
            "unit": "g",
            "quality": 1
        })

        return readings