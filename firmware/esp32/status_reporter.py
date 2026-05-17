# ============================================================
# StatusReporter - Sends heartbeat payload to {TOPIC_BASE}/status
# Payload matches spec Section 4 exactly
# ============================================================

import ujson
import utime
import machine


class StatusReporter:
    def __init__(self, mqtt_client, topic_status, device_id, fw_version):
        self.client = mqtt_client
        self.topic_status = topic_status
        self.device_id = device_id
        self.fw_version = fw_version
        self.start_time = utime.time()

    def send(self):
        import network

        wlan = network.WLAN(network.STA_IF)
        rssi = wlan.status("rssi") if wlan.isconnected() else -100

        uptime_s = utime.time() - self.start_time

        try:
            heap_free = gc.mem_free()
        except Exception:
            heap_free = 0

        payload = {
            "device_id": self.device_id,
            "status": "online",
            "rssi": rssi,
            "heap_free": heap_free,
            "uptime_s": uptime_s,
            "ts": utime.time() * 1000,
            "fw_version": self.fw_version
        }

        result = self.client.publish(self.topic_status, ujson.dumps(payload), qos=1)
        if result:
            print(f"[STATUS] heartbeat sent, uptime={uptime_s}s, rssi={rssi}")
        else:
            print("[STATUS] heartbeat publish failed")
        return result