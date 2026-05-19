# IoT Forge — Edge Sense

A complete IoT platform for real-time sensor data collection, processing, and visualization.

## Overview

IoT Forge is a full-stack IoT solution that collects sensor data from ESP32 devices, processes it through a backend API, and displays it in a real-time React dashboard. It includes offline buffering, MQTT communication, anomaly detection, an RPi gateway for edge bridging, and an SSE (Server-Sent Events) live stream.

## Features

- **ESP32 Firmware**: MicroPython-based firmware with pluggable sensor drivers
- **Offline Buffering**: Survives power loss with up to 500 buffered readings
- **MQTT Integration**: TLS support, auto-reconnection with exponential backoff
- **Device Simulator**: Test tool for simulating multiple devices with anomaly injection
- **RPi Gateway**: Bridge for local MQTT to upstream systems with payload enrichment
- **Backend API**: FastAPI with async SQLite, REST endpoints, and SSE streaming
- **Real-time Dashboard**: React + Recharts with live updates via Server-Sent Events
- **Event Bus**: Thread-safe pub/sub for pushing MQTT messages to SSE clients
- **CrewAI Integration**: AI-powered task planning and project management

## Architecture

```
ESP32 Device ──MQTT──→ Mosquitto Broker ──→ RPi Gateway ──→ Cloud MQTT (optional)
                          :1883                (enrich + buffer)
                            │
                            ▼
                     Backend API (FastAPI)
                     ┌─────────┼─────────┬────────────┐
                     │         │         │            │
                  SQLite    EventBus    REST API   /metrics
                  (async)   (pub/sub)   (/api/v1) (Prometheus)
                                     │            │
                                     ▼            ▼
                            React Dashboard   Prometheus
                            (SSE stream)      :9090
                                                │
                                                ▼
                                            Grafana
                                            :3030
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full diagram.

## Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for simulator/gateway)
- Node.js 18+ (for dashboard development)
- MQTT broker (included via Docker)

## Quick Start

### 1. Start All Services

```bash
# Clone and navigate to project
cd month1-edge-sense

# Start infrastructure
docker-compose up -d --build

# Verify services
docker-compose ps
```

Expected output:
```
NAME                IMAGE                    STATUS
iot-forge-mosquitto eclipse-mosquitto:2.0.18  Up
iot-forge-backend   backend:latest           Up
iot-forge-dashboard dashboard:latest         Up
```

### 2. Verify Backend

```bash
curl http://localhost:8000/api/v1/health
```

Expected:
```json
{
  "status": "ok",
  "ts": 1716000000000,
  "device_count": 0
}
```

### 3. Start Simulator (Generate Test Data)

```bash
# Install dependencies
pip install -r firmware/simulator/requirements.txt

# Run simulator with 3 devices
python firmware/simulator/simulator.py --devices 3 --interval 2
```

### 4. View Dashboard

Open: http://localhost:3000

You should see:
- Device list on the left
- Live sensor readings (temperature, humidity, vibration)
- Real-time updating charts

### 5. Check Data via API

```bash
# List devices
curl http://localhost:8000/api/v1/devices | python -m json.tool

# Get latest readings
curl http://localhost:8000/api/v1/readings/latest | python -m json.tool

# Query with filters
curl "http://localhost:8000/api/v1/readings?sensor=temperature&limit=5"

# SSE live stream (press Ctrl+C to stop)
curl -N http://localhost:8000/api/v1/stream
```

## Project Structure

```
month1-edge-sense/
├── firmware/
│   ├── esp32/                  # ESP32 MicroPython firmware
│   │   ├── main.py             # Main event loop
│   │   ├── mqtt_client.py      # MQTT client with TLS + backoff
│   │   ├── local_buffer.py     # Offline data buffer (filesystem)
│   │   ├── sensor_registry.py  # Dynamic driver loader
│   │   ├── status_reporter.py  # Heartbeat publisher
│   │   ├── drivers/            # Sensor drivers
│   │   │   ├── dht22.py
│   │   │   ├── mpu6050.py
│   │   │   └── adc_generic.py
│   │   └── config.json
│   ├── simulator/              # Device simulator (Python)
│   │   ├── simulator.py
│   │   └── requirements.txt
│   └── rpi_gateway/            # RPi MQTT gateway
│       ├── gateway.py          # Full gateway implementation
│       ├── gateway_config.yaml # Configuration file
│       └── requirements.txt
├── backend/                    # FastAPI backend
│   ├── main.py                 # App entry point (lifespan, CORS, routers)
│   ├── database.py             # Async SQLite (aiosqlite)
│   ├── mqtt_subscriber.py      # Background MQTT listener
│   ├── event_bus.py            # Thread-safe pub/sub for SSE
│   ├── models.py               # Pydantic models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── routers/
│       ├── __init__.py
│       ├── devices.py          # GET /api/v1/devices
│       ├── readings.py         # GET /api/v1/readings, /readings/latest
│       └── stream.py           # GET /api/v1/stream (SSE)
├── dashboard/                  # React dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── DeviceList.jsx
│   │   │   ├── GaugeCard.jsx
│   │   │   ├── SensorChart.jsx
│   │   │   └── StatusBadge.jsx
│   │   ├── hooks/
│   │   │   └── useSensorStream.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   └── package.json
├── crewai/                    # AI task planning
├── tests/                     # Test suite
│   ├── test_sensor_drivers.py # 4 tests (driver validation)
│   ├── test_simulator.py      # 6 tests (model behavior)
│   ├── test_api.py            # 5 tests (REST + SSE)
│   ├── test_mqtt_schema.py    # 8 tests (topic/payload validation)
│   ├── conftest.py
│   └── pytest.ini
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md
│   ├── MQTT_SCHEMA.md
│   └── DEMO_SCRIPT.md
├── prometheus/                # Prometheus monitoring
│   ├── prometheus.yml
│   └── rules/
│       └── iot_alerts.yml     # Alerting rules
├── grafana/                   # Grafana dashboards
│   ├── dashboards/
│   │   └── iot-forge-dashboard.json
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml
│       └── dashboards/
│           └── dashboards.yml
├── docker-compose.yml
├── mosquitto.conf
├── Makefile
└── pytest.ini
```

## Configuration

### MQTT Broker

Edit `mosquitto.conf` or use defaults (port 1883).

### Backend Environment

```bash
# Optional: Override defaults
export MQTT_HOST=localhost
export MQTT_PORT=1883
export DB_PATH=/data/iot_data.db
```

### RPi Gateway

Edit `firmware/rpi_gateway/gateway_config.yaml`:

```yaml
gateway:
  id: "rpi-gw-001"
  org_id: "demo"
  site_id: "blr-demo"

local_broker:
  host: "localhost"
  port: 1883

upstream_broker:
  enabled: false   # set true + fill credentials to bridge to cloud
  host: "YOUR_CLOUD_BROKER_HOST"
  port: 8883
  username: ""
  password: ""

buffer_size: 10000        # max in-memory buffered messages
stats_interval_s: 30      # stats log interval
api_port: 8080            # /health and /devices HTTP port
```

### ESP32 Configuration

Edit `firmware/esp32/config.json`:

```json
{
  "wifi": {
    "ssid": "YOUR_WIFI_SSID",
    "password": "YOUR_WIFI_PASSWORD"
  },
  "mqtt": {
    "host": "mqtt-broker-host",
    "port": 1883
  },
  "interval_ms": 5000,
  "sensors": [...]
}
```

## API Endpoints

| Method | Path                    | Description                        |
|--------|-------------------------|------------------------------------|
| GET    | `/api/v1/health`        | Health check (status, ts, count)   |
| GET    | `/api/v1/devices`       | List all known devices             |
| GET    | `/api/v1/readings`      | Query readings (filters below)     |
| GET    | `/api/v1/readings/latest` | Latest reading per device+sensor |
| GET    | `/api/v1/stream`        | SSE live stream of sensor data     |

### Query Parameters for `/api/v1/readings`

| Param      | Type    | Description                        |
|------------|---------|------------------------------------|
| device_id  | string  | Filter by device ID                |
| sensor     | string  | Filter by sensor type              |
| limit      | integer | Max results (1-5000, default 200)  |
| since_ts   | integer | Only readings >= this Unix ms ts   |

## Monitoring (Prometheus + Grafana)

The backend exposes Prometheus metrics at `GET /metrics` (port 8000).

### Metrics Available

| Metric                          | Type      | Labels                                      | Description                        |
|---------------------------------|-----------|---------------------------------------------|------------------------------------|
| `sensor_readings_total`         | Counter   | `device_id`, `org_id`, `site_id`, `sensor`  | Total sensor readings ingested     |
| `sensor_reading_value`          | Gauge     | `device_id`, `sensor`, `unit`               | Latest sensor reading value        |
| `iot_device_online`             | Gauge     | `device_id`                                 | Device online status (1/0)         |
| `mqtt_messages_received_total`  | Counter   | `topic`                                     | MQTT messages by topic             |
| `mqtt_messages_processed`       | Counter   | —                                           | Successfully processed messages    |
| `database_readings_count`       | Gauge     | —                                           | Total readings in DB               |
| `database_devices_count`        | Gauge     | —                                           | Total known devices                |
| `http_request_duration_seconds` | Histogram | `method`, `path`, `status`                  | Request latency                    |
| `http_requests_total`           | Counter   | `method`, `path`, `status`                  | Total HTTP requests                |

### Access Monitoring Stack

With `docker-compose up -d`:

| Service    | URL                          | Credentials     |
|------------|------------------------------|-----------------|
| Prometheus | http://localhost:9090        | —               |
| Grafana    | http://localhost:3030        | admin / admin   |
| Backend    | http://localhost:8000/metrics | —               |

### RPi Gateway Metrics

If the RPi gateway is running (port 8080), it exposes its own `/metrics` endpoint:

| Metric                             | Type    | Labels                                         | Description                        |
|------------------------------------|---------|------------------------------------------------|------------------------------------|
| `gateway_info`                     | Gauge   | `id`, `org_id`, `site_id`                      | Gateway metadata (always 1)        |
| `gateway_up_connected`             | Gauge   | —                                              | Upstream connection status (1/0)   |
| `gateway_known_devices`            | Gauge   | —                                              | Number of tracked edge devices     |
| `gateway_buffer_size`              | Gauge   | —                                              | Current buffered message count     |
| `gateway_messages_forwarded_total` | Counter | —                                              | Messages forwarded to upstream     |
| `gateway_messages_buffered_total`  | Counter | —                                              | Messages buffered when offline     |
| `gateway_buffer_dropped_total`     | Counter | —                                              | Messages dropped due to full buffer|
| `gateway_uptime_seconds`           | Gauge   | —                                              | Process uptime                     |

Add a scrape target in `prometheus/prometheus.yml` for the gateway:
```yaml
  - job_name: 'iot-forge-gateway'
    static_configs:
      - targets: ['<pi-ip>:8080']
    metrics_path: /metrics
```

### Grafana Dashboard

A pre-provisioned dashboard is available at `grafana/dashboards/iot-forge-dashboard.json` with sections for:

**Backend Stats** (top row):
- Readings/min, Active Devices, MQTT Msgs/min, Total DB Readings, API Req/s, API Latency p95

**RPi Gateway** (second row):
- Upstream Status (Connected/Disconnected), Buffer Size, Buffer Dropped, Known Devices, Forwarded/s, Buffered/s

**Sensor Time-Series** (bottom):
- Temperature, Humidity, Vibration RMS, Current — per-device line charts

### Prometheus Alerting Rules

Rules are defined in `prometheus/rules/iot_alerts.yml`:

| Alert                | Condition                          | Severity |
|----------------------|------------------------------------|----------|
| BackendDown          | Backend unreachable > 1m           | critical |
| NoReadingsReceived   | Zero readings in 5m                | warning  |
| DeviceOffline        | Device offline > 5m                | warning  |
| HighTemperature      | Temperature > 50°C                 | warning  |
| HighVibration        | Vibration RMS > 0.3g               | warning  |

### Grafana Dashboard

A pre-provisioned dashboard is available at `grafana/dashboards/iot-forge-dashboard.json` with panels for:
- Readings per minute
- Active devices
- MQTT message rate
- Total DB readings
- Temperature, humidity, vibration, current time-series

## MQTT Topic Schema

See [docs/MQTT_SCHEMA.md](docs/MQTT_SCHEMA.md) for complete topic and payload specifications.

The RPi Gateway enriches every payload with:
- `_gw_ts`  — gateway receive timestamp (Unix ms)
- `_gw_id`  — gateway device ID (e.g. `rpi-gw-001`)
- `_gw_site` — site ID from gateway config

## Running Components Individually

### Backend Only

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Dashboard Dev Mode

```bash
cd dashboard
npm install
npm run dev
```

### Simulator Only

```bash
pip install -r firmware/simulator/requirements.txt
python firmware/simulator/simulator.py --devices 3 --interval 2 --anomaly
```

### Gateway Only

```bash
pip install -r firmware/rpi_gateway/requirements.txt
python firmware/rpi_gateway/gateway.py
```

The gateway requires a running MQTT broker (Mosquitto) on `localhost:1883`.

## Testing

```bash
# Run all tests (from month1-edge-sense/)
pytest tests/ -v
```

Expected test suites:

| Test file              | Tests | Description               |
|------------------------|-------|---------------------------|
| `test_sensor_drivers.py` | 4    | Sensor driver validation  |
| `test_simulator.py`      | 6    | SensorModel behavior      |
| `test_api.py`            | 5    | REST endpoints + SSE      |
| `test_mqtt_schema.py`    | 8    | Topic/payload validation  |

## Anomaly Detection

The simulator can inject anomalies after 30 seconds:

```bash
python firmware/simulator/simulator.py --devices 2 --interval 2 --anomaly
```

After 30 seconds, vibration readings will exceed 0.30g, visible in the dashboard.

## WSL (Windows Subsystem for Linux)

When running Docker via WSL, the containers run inside WSL's VM, not on Windows directly.

### Accessing services from Windows browser

Use WSL's IP address instead of `localhost`:
```powershell
# From Windows PowerShell
wsl -- ip addr show eth0 | grep -Po 'inet \K[\d.]+'
```

Or use port forwarding (already set up by Docker Desktop automatically in most cases).

### NO DATA in Prometheus

If Prometheus shows "NO DATA":

1. **Check backend is running and healthy:**
   ```bash
   docker-compose ps
   docker-compose logs backend
   ```

2. **Test the /metrics endpoint directly:**
   ```bash
   curl -s http://localhost:8000/metrics | head -20
   ```

3. **Verify Prometheus can reach the backend:**
   ```bash
   docker-compose exec prometheus wget -qO- http://iot-forge-backend:8000/metrics | head -10
   ```
   If this fails, check Prometheus target status at http://localhost:9090/targets

4. **Check Prometheus target status in UI:**
   Open http://localhost:9090/targets — look for `iot-forge-backend` job. If it shows `DOWN`, the endpoint is unreachable.

5. **Restart cleanly:**
   ```bash
   docker-compose down -v
   docker-compose up -d --build
   ```

### Service name resolution

Docker Compose containers resolve each other by **service name** or **container_name**. In prometheus.yml the target `iot-forge-backend:8000` resolves to the backend container because its `container_name` is `iot-forge-backend`.

### File permission issues

If volume mounts cause permission errors:
```bash
# Fix grafana data permissions
sudo chown -R 472:472 grafana/
```

## Troubleshooting

### Services won't start

```bash
docker-compose logs
```

### No data in dashboard

1. Check simulator is running
2. Verify backend can connect to MQTT
3. Check browser console for errors

### Port conflicts

Edit `docker-compose.yml` to change ports:
- mosquitto: 1883
- backend: 8000
- dashboard: 3000
- prometheus: 9090
- grafana: 3030

## Development

### Adding New Sensor

1. Create driver in `firmware/esp32/drivers/`
2. Register in `config.json`
3. No code changes to main.py needed

### Adding API Endpoint

1. Create router in `backend/routers/`
2. Import and include in `backend/main.py`

### Extending Dashboard

- Add components in `dashboard/src/components/`
- Use SSE hook in `dashboard/src/hooks/useSensorStream.js`

## License

MIT License - see LICENSE file.

## Support

- Documentation: [docs/](docs/)
- MQTT Schema: [docs/MQTT_SCHEMA.md](docs/MQTT_SCHEMA.md)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Demo Scripts: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
