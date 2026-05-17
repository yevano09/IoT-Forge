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
                    │  Gateway   │         │  (Testing)  │        │   API       │
                    └──────┬──────┘         └─────────────┘        └──────┬──────┘
                           │                                                   │
                    ┌──────┴──────┐                                    ┌───────┴────────┐
                    │ Enrichment  │                                    │   MQTT        │
                    │ + Buffering │                                    │   Subscriber  │
                    └─────────────┘                                    └───────┬────────┘
                                                                          │
                                                              ┌───────────┼───────────┐
                                                              │           │           │
                                                        ┌─────┴────┐  ┌─┴────┐  ┌──┴─────┐
                                                        │  SQLite  │  │ Event│  │ REST   │
                                                        │   DB     │  │ Bus  │  │  API   │
                                                        └──────────┘  └──────┘  └────────┘
                                                                                   │
                                                                        ┌──────────┴──────────┐
                                                                        │     Dashboard      │
                                                                        │   (React + SSE)    │
                                                                        │    localhost:3000  │
                                                                        └────────────────────┘
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
- Realistic sensor data generation
- Anomaly injection (vibration > 0.30g after 30s)
- MQTT publishing with proper schema

**Usage:**
```bash
python simulator.py --devices 3 --interval 2 --anomaly
```

### RPi Gateway (firmware/rpi_gateway/)

Bridge between local MQTT broker and upstream systems.

**Features:**
- Subscribes to local broker
- Payload enrichment with gateway metadata
- Offline buffering to upstream
- HTTP health endpoints (/health, /devices)

### Backend API (backend/)

FastAPI-based data ingestion and REST API server.

**Endpoints:**
- `GET /api/v1/health` - Health check
- `GET /api/v1/devices` - List devices
- `GET /api/v1/devices/{id}` - Device details
- `GET /api/v1/readings` - Query readings
- `GET /api/v1/readings/latest` - Latest readings
- `GET /api/v1/stream` - SSE real-time stream

**Components:**
- `main.py`: FastAPI app with lifespan
- `database.py`: Async SQLite with aiosqlite
- `mqtt_subscriber.py`: Background MQTT listener
- `models.py`: Pydantic models
- `routers/`: API route handlers

### React Dashboard (dashboard/)

Real-time monitoring web interface.

**Features:**
- SSE-based real-time updates
- Device list with status badges
- Gauge cards for current values
- Historical line charts (Recharts)
- Auto-reconnect on disconnect

### Infrastructure

**Docker Compose:**
- Mosquitto MQTT broker
- Backend API service
- React dashboard (nginx)

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

## Data Retention

| Component   | Retention    | Storage       |
|-------------|--------------|---------------|
| SQLite Dev  | 30 days      | File          |
| TimescaleDB | Configurable | Table Partitioning |
| Dashboard   | Last 100 readings | In-memory    |

## Security

- TLS/SSL for MQTT connections (configurable)
- No authentication in default config (use in production)
- API CORS: allows all origins (configure for production)
- Device IDs: use unique identifiers (MAC or UUID)