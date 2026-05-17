# ============================================================
# Prometheus Metrics Module
# ============================================================

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# MQTT metrics
mqtt_messages_received = Counter(
    'mqtt_messages_received_total',
    'Total MQTT messages received',
    ['topic']
)

mqtt_messages_processed = Counter(
    'mqtt_messages_processed_total',
    'Total MQTT messages processed successfully'
)

mqtt_connection_errors = Counter(
    'mqtt_connection_errors_total',
    'Total MQTT connection errors'
)

# Sensor data metrics
sensor_readings = Gauge(
    'sensor_reading_value',
    'Current sensor reading value',
    ['device_id', 'org_id', 'site_id', 'sensor', 'unit']
)

sensor_readings_total = Counter(
    'sensor_readings_total',
    'Total sensor readings received',
    ['device_id', 'sensor', 'quality']
)

# Device metrics
devices_registered = Gauge(
    'iot_devices_registered',
    'Number of registered devices'
)

device_online = Gauge(
    'iot_device_online',
    'Device online status (1=online, 0=offline)',
    ['device_id']
)

# Database metrics
db_readings_count = Gauge(
    'database_readings_count',
    'Total number of readings in database'
)

db_operations_duration_seconds = Histogram(
    'database_operations_duration_seconds',
    'Database operation duration in seconds',
    ['operation']
)

# Business metrics
alerts_triggered = Counter(
    'alerts_triggered_total',
    'Total alerts triggered',
    ['alert_type', 'severity']
)


def get_metrics():
    """Generate Prometheus metrics output"""
    return generate_latest()


def record_request(method: str, endpoint: str, status: int):
    """Record HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()


def record_mqtt_message(topic: str):
    """Record MQTT message received"""
    mqtt_messages_received.labels(topic=topic).inc()


def record_sensor_reading(device_id: str, org_id: str, site_id: str, sensor: str, value: float, unit: str):
    """Record sensor reading value"""
    sensor_readings.labels(
        device_id=device_id,
        org_id=org_id,
        site_id=site_id,
        sensor=sensor,
        unit=unit
    ).set(value)

    sensor_readings_total.labels(
        device_id=device_id,
        sensor=sensor,
        quality="1"
    ).inc()


def update_device_count(count: int):
    """Update registered devices count"""
    devices_registered.set(count)


def set_device_online(device_id: str, online: bool):
    """Set device online status"""
    device_online.labels(device_id=device_id).set(1 if online else 0)