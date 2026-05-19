try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
    _HAVE_PROMETHEUS = True
except ImportError:
    _HAVE_PROMETHEUS = False

    class _Noop:
        def inc(self, *a, **kw): pass
        def set(self, *a, **kw): pass
        def observe(self, *a, **kw): pass
        def labels(self, *a, **kw): return _Noop()

    Counter = Gauge = Histogram = _Noop

    def _fake_latest(*a, **kw): return b""

    generate_latest = _fake_latest
    REGISTRY = None

sensor_readings_total = Counter(
    "sensor_readings_total",
    "Total sensor readings ingested",
    ["device_id", "org_id", "site_id", "sensor"]
)

mqtt_messages_received_total = Counter(
    "mqtt_messages_received_total",
    "MQTT messages received by topic",
    ["topic"]
)

mqtt_messages_processed = Counter(
    "mqtt_messages_processed",
    "MQTT messages successfully processed"
)

iot_device_online = Gauge(
    "iot_device_online",
    "Device online status (1=online, 0=offline)",
    ["device_id"]
)

database_readings_count = Gauge(
    "database_readings_count",
    "Total number of readings in the database"
)

database_devices_count = Gauge(
    "database_devices_count",
    "Total number of known devices"
)

sensor_reading_value = Gauge(
    "sensor_reading_value",
    "Latest sensor reading value",
    ["device_id", "sensor", "unit"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path", "status"]
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)


def record_sensor_reading(device_id: str, org_id: str, site_id: str, sensor: str, value: float, unit: str):
    sensor_readings_total.labels(device_id, org_id, site_id, sensor).inc()
    sensor_reading_value.labels(device_id, sensor, unit).set(value)


def set_device_online(device_id: str, online: bool):
    iot_device_online.labels(device_id).set(1 if online else 0)


def record_mqtt_message(topic: str):
    mqtt_messages_received_total.labels(topic).inc()


def record_request(method: str, path: str, status_code: int):
    http_requests_total.labels(method, path, str(status_code)).inc()


def record_request_duration(method: str, path: str, status_code: int, duration: float):
    http_request_duration_seconds.labels(method, path, str(status_code)).observe(duration)


def get_metrics():
    return generate_latest(REGISTRY).decode("utf-8")
