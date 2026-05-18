# ============================================================
# Test Simulator - Verify SensorModel output and anomaly injection
# ============================================================

import sys
import os
from unittest.mock import MagicMock

sys.modules.setdefault("paho", MagicMock())
sys.modules.setdefault("paho.mqtt", MagicMock())
sys.modules.setdefault("paho.mqtt.client", MagicMock())

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware", "simulator"))

import pytest


def make_sensor_model():
    ns = {}
    code = open(os.path.join(os.path.dirname(__file__), "..", "firmware", "simulator", "simulator.py")).read()
    exec(compile(code, "simulator.py", "exec"), ns)
    return ns["SensorModel"]


SensorModel = make_sensor_model()


class TestSensorModel:
    def test_generates_realistic_temperature(self):
        model = SensorModel("TEST-0", seed=42)
        readings = [model.temperature() for _ in range(100)]
        assert all(-40 <= t <= 80 for t in readings)

    def test_anomaly_raises_vibration(self):
        model = SensorModel("TEST-0", seed=0)
        model.trigger_anomaly()
        vibs = [model.vibration_rms() for _ in range(50)]
        assert all(v > 0.30 for v in vibs)

    def test_humidity_inverse_correlation_with_temperature(self):
        model_cold = SensorModel("COLD", seed=11)
        model_cold.temp_base = 15.0
        model_hot = SensorModel("HOT", seed=22)
        model_hot.temp_base = 40.0

        cold_hums = []
        hot_hums = []
        for _ in range(50):
            model_cold.tick()
            model_hot.tick()
            cold_hums.append(model_cold.humidity())
            hot_hums.append(model_hot.humidity())

        avg_cold = sum(cold_hums) / len(cold_hums)
        avg_hot = sum(hot_hums) / len(hot_hums)

        assert avg_cold > avg_hot, f"Expected hum(cold)={avg_cold:.2f} > hum(hot)={avg_hot:.2f}"

    def test_tick_increments_time(self):
        model = SensorModel("TICK", seed=1)
        assert model.t == 0
        model.tick()
        assert model.t == 1
        model.tick()
        assert model.t == 2

    def test_motor_current_positive(self):
        model = SensorModel("CURR", seed=5)
        currs = [model.motor_current() for _ in range(20)]
        assert all(c >= 0 for c in currs)

    def test_vibration_peak_sensible_range(self):
        model = SensorModel("PEAK", seed=7)
        peaks = [model.vibration_peak() for _ in range(20)]
        rms_vals = [model.vibration_rms() for _ in range(20)]
        assert all(p >= 0 for p in peaks)
        assert all(p >= r for p, r in zip(peaks, rms_vals))