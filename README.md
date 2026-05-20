# IoT Forge — Edge Sense

A complete, open-source IoT platform for real-time sensor monitoring. ESP32 devices publish readings over MQTT to a Mosquitto broker. A Python simulator mimics hundreds of factory sensors. A FastAPI backend ingests, stores, and streams the data. A React dashboard displays live gauges and time-series charts. Prometheus and Grafana provide production-grade alerting and dashboards. CrewAI agents assist with development tasks. This is Month 1 of a 6-month IoT platform build.

## Architecture

```
ESP32 sensors ──MQTT──> Mosquitto (local) ──> RPi Gateway ──> Cloud MQTT
Python sim    ────────/         │                                        ^
                               │                                    (or Docker Gateway
                        [Docker Gateway] ────────────────────────────  for dev testing)
                               │
                       FastAPI backend (MQTT subscriber)
                           │              │
                        SQLite         EventBus
                           │              │
                     REST API         SSE stream
                           │              │
                    React Dashboard (port 3000)
                           │
                    RPi Gateway Panel
                 (upstream status, forwarded,
                  buffered, buffer size)
```

## Quick start

```bash
git clone <repo> && cd month1-edge-sense
docker-compose up -d
python firmware/simulator/simulator.py --devices 3 --interval 2 --anomaly
# open http://localhost:3000
# open http://localhost:8000/docs
# gateway API at http://localhost:8081/health
```

Six services start automatically: Mosquitto, backend, dashboard, Prometheus, Grafana, and the RPi Gateway (Docker container). The gateway subscribes to `iot/demo/blr-demo/#`, enriches every message with `_gw_ts`, `_gw_id`, and `_gw_site` fields, and forwards upstream — exactly like a physical Raspberry Pi gateway.

## Gateway enrichment

The gateway bridges a local MQTT broker (on-device Mosquitto) to the upstream cloud broker. Each forwarded message is enriched with:

| Field | Description | Example |
|-------|-------------|---------|
| `_gw_ts` | Enrichment timestamp (ms) | `1779272796572` |
| `_gw_id` | Gateway identity | `docker-gw-001` / `rpi-gw-001` |
| `_gw_site` | Deployment site | `blr-demo` |

A `_gw_ts` guard prevents re-enriching messages that were already enriched, avoiding infinite loops when local and upstream share a broker.

### Dashboard — Gateway Panel

The sidebar shows an **RPi Gateway** section (bottom of the device list) that polls `/gw/health` every 10 seconds:

- **Upstream** — green `Connected` / red `Disconnected` dot
- **Devices** — number of unique devices the gateway has seen
- **Forwarded** — total messages forwarded to upstream
- **Buffered** — total messages buffered while offline
- **Buffer** — current buffer queue depth (turns amber when non-zero)

### Dashboard — Device List

Devices are automatically split into **online** (visible directly) and **offline** (collapsed under a `▶ Offline (N)` accordion at the bottom). Click the accordion to expand and inspect offline devices. A device is considered offline when `last_seen > 90s` ago.

## Add a new sensor in 15 minutes

**Step 1:** Create `firmware/esp32/drivers/my_sensor.py`:

```python
class Driver:
    def __init__(self, config, global_cfg):
        self.pin = config.get("data_pin")

    def read(self):
        return [{
            "sensor": "my_sensor",
            "value": 42.0,
            "unit": "custom",
            "quality": 1,
        }]
```

**Step 2:** Add one entry to `firmware/esp32/config.json`:

```json
"sensors": [
  {"driver": "my_sensor", "config": {"data_pin": 4}}
]
```

**Step 3:** Flash the device or restart the simulator. The new sensor appears in the dashboard automatically.

## Configuration reference

### `firmware/esp32/config.json`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `wifi.ssid` | string | — | Wi-Fi network name |
| `wifi.password` | string | — | Wi-Fi password |
| `mqtt.broker` | string | `"localhost"` | MQTT broker hostname |
| `mqtt.port` | int | `1883` | MQTT broker port |
| `mqtt.tls_enabled` | bool | `false` | Enable TLS for MQTT |
| `mqtt.org_id` | string | `"demo"` | Organisation ID |
| `mqtt.site_id` | string | `"site-1"` | Site ID |
| `sensors` | array | `[]` | Sensor driver configurations |
| `sensors[].driver` | string | — | Driver module name |
| `sensors[].config` | object | `{}` | Driver-specific config |
| `interval_s` | int | `5` | Reading interval in seconds |
| `buffer.max_size` | int | `500` | Max offline buffer entries |
| `status.interval_s` | int | `60` | Status heartbeat interval |

### `firmware/rpi_gateway/gateway_config.yaml`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `gateway.id` | string | — | Unique gateway identifier |
| `gateway.org_id` | string | — | Organisation ID |
| `gateway.site_id` | string | — | Site ID |
| `local_broker.host` | string | `"localhost"` | Local Mosquitto host |
| `local_broker.port` | int | `1883` | Local Mosquitto port |
| `upstream_broker.enabled` | bool | `false` | Enable cloud bridge |
| `upstream_broker.host` | string | — | Upstream broker host |
| `upstream_broker.port` | int | `8883` | Upstream broker port (TLS) |
| `upstream_broker.username` | string | `""` | Upstream broker username |
| `upstream_broker.password` | string | `""` | Upstream broker password |
| `buffer_size` | int | `10000` | Max buffered messages |
| `stats_interval_s` | int | `30` | Stats log interval |
| `api_port` | int | `8080` | Gateway API port |

## MQTT topic schema

| Topic pattern | Purpose |
|---------------|---------|
| `iot/{org}/{site}/{device}/{sensor}/raw` | Sensor reading |
| `iot/{org}/{site}/{device}/status` | Device heartbeat |
| `iot/{org}/{site}/{device}/cmd/{command}` | Command to device |
| `iot/{org}/{site}/{device}/cmd/{command}/ack` | Command acknowledgement |

### Raw reading payload

```json
{
  "device_id": "ESP32-A1B2C3",
  "org_id": "acme",
  "site_id": "blr-plant-1",
  "sensor": "temperature",
  "value": 42.7,
  "unit": "celsius",
  "quality": 1,
  "ts": 1716000000000,
  "seq": 1042,
  "fw_version": "1.0.3"
}
```

### Status payload

```json
{
  "device_id": "ESP32-A1B2C3",
  "status": "online",
  "rssi": -67,
  "heap_free": 142336,
  "uptime_s": 86400,
  "ts": 1716000000000,
  "fw_version": "1.0.3"
}
```

## REST API reference

### Backend API

| Method | Endpoint | Description | Curl example |
|--------|----------|-------------|--------------|
| GET | `/api/v1/health` | Service health | `curl http://localhost:8000/api/v1/health` |
| GET | `/api/v1/devices` | List all devices | `curl http://localhost:8000/api/v1/devices` |
| GET | `/api/v1/readings` | Query readings | `curl "http://localhost:8000/api/v1/readings?sensor=temperature&limit=5"` |
| GET | `/api/v1/readings/latest` | Latest reading per sensor | `curl http://localhost:8000/api/v1/readings/latest` |
| GET | `/api/v1/stream` | SSE live stream | `curl -N http://localhost:8000/api/v1/stream` |

### Gateway API (proxied via dashboard at `/gw/`)

| Method | Endpoint | Description | Curl example |
|--------|----------|-------------|--------------|
| GET | `/gw/health` | Gateway health & stats | `curl http://localhost:3000/gw/health` |
| GET | `/gw/devices` | Devices known to gateway | `curl http://localhost:3000/gw/devices` |
| GET | `/gw/metrics` | Prometheus metrics | `curl http://localhost:3000/gw/metrics` |

### Example response — `/api/v1/health`

```json
{"status": "ok", "ts": 1716000000000, "device_count": 3}
```

### Example response — `/api/v1/devices`

```json
[
  {"device_id": "SIM-DEVICE-0000", "status": "online", "last_seen": 1716000000000, "fw_version": "sim-1.0.0"}
]
```

### Example response — `/api/v1/readings/latest`

```json
[
  {"device_id": "SIM-DEVICE-0000", "sensor": "temperature", "value": 28.12, "unit": "celsius", "ts": 1716000000000}
]
```

### Example response — `/gw/health`

```json
{
  "status": "ok",
  "upstream_connected": true,
  "known_devices": 3,
  "buffer_size": 0,
  "forwarded": 3244,
  "buffered": 3
}
```

## Scaling to 10,000 devices

| Component | Dev | Production | Change required |
|-----------|-----|------------|-----------------|
| MQTT broker | Mosquitto (single node) | EMQX cluster | Config swap |
| Edge gateway | Docker Gateway (dev) / RPi Gateway (production) | RPi Gateway with upstream bridge | Config swap |
| Database | SQLite | TimescaleDB | `DB_PATH` → `DATABASE_URL` |
| Message buffer | In-process queue | Kafka | Config swap |
| Container orchestration | Docker Compose | Kubernetes | Helm chart |
| API gateway | None | Kong / Traefik | Add reverse proxy |

All changes are config or env-var swaps. No code changes required.

## Month 2 preview — Fleet Commander

OTA firmware updates, remote configuration push, device registry with health monitoring, firmware version tracking, and bulk command dispatch. Each device gets a maintenance history, and the dashboard gains a fleet overview with per-device controls.
