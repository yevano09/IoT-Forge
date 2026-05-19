# IoT Forge — Architecture Overview

## Full Data Flow

```
                                    ┌─────────────────┐
                                    │  ESP32 Device   │
                                    │  (MicroPython)  │
                                    └────────┬────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              │              │              │
                    ┌─────────┴───┐  ┌──────┴─────┐  ┌──────┴─────┐
                    │   DHT22     │  │  MPU6050   │  │    ADC     │
                    │ Temp/Hum    │  │ Vibration  │  │   Current  │
                    └──────┬──────┘  └──────┬─────┘  └──────┬─────┘
                           │              │              │
                           └──────────────┴──────────────┘
                                          │
                                   ┌──────┴──────┐
                                   │   Sensor    │
                                   │  Registry   │
                                   └──────┬──────┘
                                          │
                                  ┌───────┴────────┐
                                  │               │
                           ┌──────┴──────┐  ┌─────┴──────┐
                           │ LocalBuffer │  │ MQTT Client│
                           │  (500 rec)  │  │  (TLS)     │
                           └─────────────┘  └─────┬──────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │  Mosquitto  │
                                            │   Broker    │
                                            │  :1883      │
                                            └──────┬──────┘
                                                   │
                           ┌───────────────────────┼───────────────────────┐
                           │                       │                       │
                    ┌──────┴──────┐         ┌──────┴──────┐        ┌──────┴──────┐
                    │  RPi        │         │   Simulator │        │   Backend   │
                    │  Gateway    │         │  (Testing)  │        │   API       │
                    └──────┬──────┘         └─────────────┘        └──────┬──────┘
                           │                                                   │
                    ┌──────┴──────┐                                    ┌───────┴────────┐
                    │ Enrichment  │                                    │   MQTT         │
                    │ + Buffering │                                    │   Subscriber   │
                    └──────┬──────┘                                    └───────┬────────┘
                           │                                                    │
                           │                                            ┌───────┴────────┐
                           │                                            │   EventBus     │
                           │                                            │  (pub/sub)     │
                           │                                            └───────┬────────┘
                           │                                                    │
                           │                                          ┌─────────┼──────────┐
                           │                                          │         │          │
                           │                                    ┌─────┴────┐  ┌──┴─────┐  ┌──┴─────┐
                           │                                    │  SQLite  │  │  SSE   │  │ REST   │
                           │                                    │   DB     │  │ Stream │  │  API   │
                           │                                    └──────────┘  └────────┘  └────────┘
                           │                                                    │
                           │                                         ┌──────────┴──────────┐
                           │                                         │     Dashboard      │
                           │                                         │   (React + SSE)    │
                           │                                         │    localhost:3000  │
                           │                                         └────────────────────┘
                           │
                    ┌──────┴──────┐
                    │  Cloud MQTT │
                    │  (optional) │
                    └─────────────┘

                            ┌────────────┐
                            │  Backend   │
                            │  /metrics  │
                            └──────┬─────┘
                                   │
                                   ▼
                            ┌────────────┐
                            │ Prometheus │
                            │  :9090     │
                            └──────┬─────┘
                                   │
                                   ▼
                            ┌────────────┐
                            │  Grafana   │
                            │  :3030     │
                            └────────────┘
```

## Component Descriptions

### ESP32 Firmware (firmware/esp32/)

The core embedded software running on ESP32 devices.

**Modules:**
- `main.py`: Main event loop, WiFi/MQTT connection, sensor reading orchestration
- `mqtt_client.py`: MQTT client wrapper with TLS support and exponential backoff
- `local_buffer.py`: Offline data buffer using filesystem (survives power loss)
- `sensor_registry.py`: Dynamic driver loader for pluggable sensors
- `status_reporter.py`: Heartbeat/status message publisher
- `drivers/`: Sensor driver modules (dht22, mpu6050, adc_generic)

**Key Features:**
- Survives power loss with offline buffering
- Auto-reconnection with exponential backoff
- Pluggable sensor architecture
- Remote command handling

### Device Simulator (firmware/simulator/)

Python-based test tool for simulating multiple ESP32 devices.

**Features:**
- Multiple device simulation
- Realistic sensor data generation (temperature, humidity, vibration, motor current)
- Time-correlated readings (temperature inversely correlated with humidity)
- Anomaly injection (vibration > 0.30g after 30s)
- MQTT publishing with proper schema

**Usage:**
```bash
python simulator.py --devices 3 --interval 2 --anomaly
```

### RPi Gateway (firmware/rpi_gateway/)

Bridge between local MQTT broker and upstream/cloud systems. Designed to run on a Raspberry Pi at the edge site.

**Architecture:**
- Subscribes to local Mosquitto broker on `iot/{org}/{site}/#`
- Enriches every payload with gateway metadata (`_gw_ts`, `_gw_id`, `_gw_site`)
- Tracks known devices in memory (`device_id` → `last_seen`, `topic`)
- When upstream is connected: forwards messages in real-time
- When upstream is offline: buffers in an in-memory queue (`UpstreamBuffer`)
- Flushes buffer on upstream reconnect
- Exposes HTTP endpoints for health monitoring and device discovery

**HTTP Endpoints (port 8080):**
- `GET /health` — gateway health, upstream status, buffer size, stats
- `GET /devices` — known devices with last-seen timestamps

**Classes:**
- `UpstreamBuffer`: Thread-safe bounded queue with non-blocking put and drop counting
- `Gateway`: Main orchestrator — local broker client, upstream client, stats loop, API loop

**HTTP Endpoints (port 8080):**
- `GET /health` — gateway health, upstream status, buffer size, stats
- `GET /devices` — known devices with last-seen timestamps
- `GET /metrics` — Prometheus metrics (exposition format, stdlib, no external deps)

**Prometheus Metrics:**
| Metric                             | Description                        |
|------------------------------------|------------------------------------|
| `gateway_info`                     | Gateway metadata labels            |
| `gateway_up_connected`             | Upstream connection status         |
| `gateway_known_devices`            | Number of tracked edge devices     |
| `gateway_buffer_size`              | Current buffered message count     |
| `gateway_messages_forwarded_total` | Total forwarded upstream           |
| `gateway_messages_buffered_total`  | Total buffered when offline        |
| `gateway_buffer_dropped_total`     | Dropped due to full buffer         |
| `gateway_uptime_seconds`           | Process uptime                     |

**Config file:** `gateway_config.yaml`

### Backend API (backend/)

FastAPI-based data ingestion, storage, and streaming server.

**Additional Endpoints:**
- `GET /metrics` — Prometheus metrics from `backend/metrics.py` (9 metric families)

**Endpoints (all under `/api/v1`):**

| Method | Path                    | Description                               |
|--------|-------------------------|-------------------------------------------|
| GET    | `/api/v1/health`        | Health check: `{status, ts, device_count}`|
| GET    | `/api/v1/devices`       | List all known devices (sorted by last_seen) |
| GET    | `/api/v1/readings`      | Query time-series readings (filtered, paginated) |
| GET    | `/api/v1/readings/latest` | Most recent reading per device+sensor    |
| GET    | `/api/v1/stream`        | SSE live stream — pushes every new reading |

**Components:**
- `main.py`: FastAPI app with lifespan (init DB, start MQTT subscriber), CORS middleware, router mounting
- `database.py`: Async SQLite via aiosqlite — `Database` class with `init()`, `insert_reading()`, `upsert_device()`, `get_readings()`, `get_latest_readings()`, `get_devices()`, `device_count()`
- `mqtt_subscriber.py`: Paho MQTT client running in a background thread. Routes messages:
  - `/status` topic → `db.upsert_device()` (async via `run_coroutine_threadsafe`)
  - `/raw` topic → `db.insert_reading()` + `bus.publish()` (async + thread-safe pub)
- `event_bus.py`: Thread-safe pub/sub with `asyncio.Queue` per subscriber. The `publish()` method is called from the MQTT thread and fans out to all SSE client queues.
- `models.py`: Pydantic models (`SensorReading`, `DeviceStatus`, `HealthResponse`)
- `routers/devices.py`: Device listing router
- `routers/readings.py`: Reading query/latest router
- `routers/stream.py`: SSE streaming router with 30s keepalive

**Data Flow (MQTT → DB → SSE):**

```
MQTT message arrives (paho thread)
  → _on_message() parses JSON
  → asyncio.run_coroutine_threadsafe(db.insert_reading(), loop)
  → bus.publish(payload)  (non-blocking, thread-safe)
     → fans out to all SSE subscriber queues
        → event_generator() yields "data: {json}\n\n"
```

**Testing:**
```bash
cd month1-edge-sense
pytest tests/test_api.py -v
```

### React Dashboard (dashboard/)

Real-time monitoring web interface.

**Features:**
- SSE-based real-time updates (hooks/useSensorStream.js)
- Device list with status badges
- Gauge cards for current values (temperature, humidity, vibration, current)
- Historical line charts (Recharts)
- Auto-reconnect on disconnect
- Device selection and filtering

### Infrastructure

**Docker Compose services:**
- Mosquitto MQTT broker (port 1883)
- Backend API service (port 8000) — also exposes `/metrics`
- React dashboard served via nginx (port 3000)
- Prometheus (port 9090) — scrapes `/metrics` every 15s, evaluates alerting rules
- Grafana (port 3030) — pre-provisioned with Prometheus datasource and IoT dashboard

**Supporting files:**
- `mosquitto.conf` — broker configuration (anonymous access, persistence)
- `Makefile` — convenience commands (up, down, logs, test, health)

## Gateway Enrichment

The RPi Gateway adds these fields to every forwarded payload:

| Field     | Description                        | Example          |
|-----------|------------------------------------|------------------|
| `_gw_ts`  | Gateway receive timestamp (Unix ms)| 1716000000123    |
| `_gw_id`  | Gateway device ID                  | "rpi-gw-001"     |
| `_gw_site`| Site ID from gateway config        | "blr-demo"       |

This allows the backend to distinguish between readings from different gateways/sites even if device IDs overlap.

## Data Retention

| Component   | Retention    | Storage       |
|-------------|--------------|---------------|
| SQLite Dev  | Unlimited (manual cleanup) | File |
| Dashboard   | Last 100 readings | In-memory    |

## Security

- TLS/SSL for MQTT connections (configurable on both ESP32 and gateway)
- No authentication in default config (configure for production)
- API CORS: allows all origins (configure for production)
- Device IDs: use unique identifiers (MAC or UUID)

## Scale-Out Notes

### Small Scale (< 100 devices)
- Single Mosquitto broker
- SQLite database
- Single backend instance

### Medium Scale (100-10,000 devices)
- EMQX or EMQ X broker
- TimescaleDB for time-series
- Load-balanced backend instances
- RPi gateways per site

### Large Scale (> 10,000 devices)
- AWS IoT Core or GCP IoT Core
- InfluxDB or TimescaleDB cluster
- Kubernetes-based backend
- Edge computing at sites
- Message queue for ingestion (Kafka)
