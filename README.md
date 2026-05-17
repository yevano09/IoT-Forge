# IoT Forge — Edge Sense

A complete IoT platform for real-time sensor data collection, processing, and visualization.

## Overview

IoT Forge is a full-stack IoT solution that collects sensor data from ESP32 devices, processes it through a backend API, and displays it in a real-time React dashboard. It includes offline buffering, MQTT communication, and anomaly detection capabilities.

## Features

- **ESP32 Firmware**: MicroPython-based firmware with pluggable sensor drivers
- **Offline Buffering**: Survives power loss with up to 500 buffered readings
- **MQTT Integration**: TLS support, auto-reconnection with exponential backoff
- **Device Simulator**: Test tool for simulating multiple devices with anomaly injection
- **RPi Gateway**: Bridge for local MQTT to upstream systems
- **Backend API**: FastAPI with async SQLite, REST endpoints, and SSE streaming
- **Real-time Dashboard**: React + Recharts with live updates via Server-Sent Events
- **CrewAI Integration**: AI-powered task planning and project management

## Architecture

```
ESP32 Device → MQTT → Backend API → Dashboard
                        ↓
                   SQLite DB
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
  "status": "healthy",
  "mqtt_connected": true,
  "db_status": "connected",
  "uptime_s": 10.5,
  "readings_count": 0,
  "devices_count": 0
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
```

## Project Structure

```
month1-edge-sense/
├── firmware/
│   ├── esp32/          # ESP32 MicroPython firmware
│   │   ├── main.py
│   │   ├── mqtt_client.py
│   │   ├── local_buffer.py
│   │   ├── sensor_registry.py
│   │   ├── status_reporter.py
│   │   ├── drivers/   # Sensor drivers
│   │   └── config.json
│   ├── simulator/      # Device simulator
│   └── rpi_gateway/    # MQTT gateway
├── backend/            # FastAPI backend
│   ├── main.py
│   ├── database.py
│   ├── mqtt_subscriber.py
│   ├── models.py
│   └── routers/
├── dashboard/          # React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── App.jsx
│   └── package.json
├── crewai/            # AI task planning
├── tests/             # Test suite
├── docs/              # Documentation
│   ├── MQTT_SCHEMA.md
│   ├── ARCHITECTURE.md
│   └── DEMO_SCRIPT.md
├── docker-compose.yml
├── mosquitto.conf
└── Makefile
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

## Running Components Individually

### Backend Only

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
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
python firmware/rpi_gateway/gateway.py firmware/rpi_gateway/gateway_config.yaml
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v
pytest tests/test_mqtt_schema.py -v
```

## Available Commands (Makefile)

```bash
make help          # Show all commands
make up            # Start services
make down          # Stop services
make logs          # View logs
make test          # Run tests
make clean         # Clean up containers and images
make health         # Check API health
make devices        # List devices via API
make readings       # Get latest readings
```

## MQTT Topic Schema

See [docs/MQTT_SCHEMA.md](docs/MQTT_SCHEMA.md) for complete topic and payload specifications.

## Anomaly Detection

The simulator can inject anomalies after 30 seconds:

```bash
python firmware/simulator/simulator.py --devices 2 --interval 2 --anomaly
```

After 30 seconds, vibration readings will exceed 0.30g, visible in the dashboard.

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