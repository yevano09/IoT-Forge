# ============================================================
# MPU-6050 I2C Accelerometer Driver
# Returns vibration_rms and vibration_peak in g
# ============================================================
#
# Wiring:
#   - VCC -> 3.3V, GND -> GND, SDA -> sda_pin, SCL -> scl_pin
#   - 4.7kOhm pull-up resistors on SDA and SCL to 3.3V
#   - AD0 -> GND for address 0x68 (default)
#
# Interface:
#   class Driver:
#     def __init__(self, pin_config: dict, options: dict): ...
#     def read(self) -> list: ...
# ============================================================

import machine
import utime
import math


MPU_ADDR     = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B


class Driver:
    def __init__(self, pin_config: dict, options: dict):
        sda = pin_config.get("sda_pin", 21)
        scl = pin_config.get("scl_pin", 22)
        self._i2c = machine.I2C(0, sda=machine.Pin(sda), scl=machine.Pin(scl), freq=400000)
        self._addr = MPU_ADDR
        self._samples = options.get("samples", 10)
        range_map = {2: 16384.0, 4: 8192.0, 8: 4096.0, 16: 2048.0}
        self._scale = range_map.get(options.get("range_g", 2), 16384.0)
        self._i2c.writeto_mem(self._addr, PWR_MGMT_1, bytes([0]))

    def _read_accel_raw(self) -> tuple:
        data = self._i2c.readfrom_mem(self._addr, ACCEL_XOUT_H, 6)
        ax = (data[0] << 8) | data[1]
        ay = (data[2] << 8) | data[3]
        az = (data[4] << 8) | data[5]
        if ax > 32767:
            ax -= 65536
        if ay > 32767:
            ay -= 65536
        if az > 32767:
            az -= 65536
        return (ax / self._scale, ay / self._scale, az / self._scale)

    def read(self) -> list:
        try:
            raw_samples = []
            for _ in range(self._samples):
                ax, ay, az = self._read_accel_raw()
                raw_samples.append((ax, ay, az))
                utime.sleep_ms(2)

            az_mean = sum(s[2] for s in raw_samples) / len(raw_samples)
            mags = []
            for ax, ay, az in raw_samples:
                mag = math.sqrt(ax * ax + ay * ay + (az - az_mean) ** 2)
                mags.append(mag)

            rms  = round(math.sqrt(sum(m * m for m in mags) / len(mags)), 4)
            peak = round(max(mags), 4)
            return [
                {"sensor": "vibration_rms",  "value": rms,  "unit": "g", "quality": 1},
                {"sensor": "vibration_peak", "value": peak, "unit": "g", "quality": 1},
            ]
        except Exception as e:
            print(f"[MPU6050] read error: {e}")
            return [
                {"sensor": "vibration_rms",  "value": None, "unit": "g", "quality": 0},
                {"sensor": "vibration_peak", "value": None, "unit": "g", "quality": 0},
            ]