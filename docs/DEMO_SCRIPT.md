# IoT Forge — Demo Script

Three versions for different presentation lengths.

---

## Setup Checklist (All Versions)

- [ ] Docker and Docker Compose installed
- [ ] Ports 1883, 8000, 3000 available
- [ ] Terminal opened in project root

```bash
cd month1-edge-sense
```

---

## 5-Minute Demo (Express)

**Goal:** Show the complete system working end-to-end.

### Step 1: Start Services (1 min)

```bash
docker-compose up -d --build
```

Wait for all services to be healthy:
```bash
docker-compose ps
```

### Step 2: Verify Backend (30 sec)

```bash
curl http://localhost:8000/api/v1/health
```

Expected: `{"status": "ok", "ts": 1716000000000, "device_count": 0}`

### Step 3: Start Simulator (2 min)

```bash
# Terminal 2
pip install -r firmware/simulator/requirements.txt
python firmware/simulator/simulator.py --devices 1 --interval 3
```

Let it run for 30 seconds to generate data.

### Step 4: Show Data in Dashboard (1 min)

Open browser: http://localhost:3000

Show:
- Device appears in device list
- Real-time values updating
- Charts populating

### Step 5: Show API Data (30 sec)

```bash
curl http://localhost:8000/api/v1/devices | python -m json.tool
curl http://localhost:8000/api/v1/readings/latest | python -m json.tool
curl -N http://localhost:8000/api/v1/stream   # Ctrl+C after a few events
```

### Cleanup

```bash
docker-compose down
```

---

## 15-Minute Demo (Standard)

**Goal:** Full walkthrough of all components.

### Part 1: Infrastructure (3 min)

Explain docker-compose.yml structure:
- Mosquitto broker
- Backend API
- Dashboard

```bash
docker-compose up -d
docker-compose logs -f mosquitto
```

### Part 2: Backend Deep Dive (4 min)

Show API endpoints:
```bash
# Health
curl http://localhost:8000/api/v1/health

# Devices
curl http://localhost:8000/api/v1/devices

# Readings with filters
curl "http://localhost:8000/api/v1/readings?sensor=temperature&limit=5"

# SSE live stream (show 3 events)
timeout 10 curl -N http://localhost:8000/api/v1/stream
```

Show database schema:
```bash
# Check SQLite
sqlite3 edge_sense.db ".tables"
sqlite3 edge_sense.db ".schema readings"
```

### Part 3: Simulator and Anomaly (4 min)

Start simulator with anomaly injection:
```bash
python firmware/simulator/simulator.py --devices 2 --interval 2 --anomaly
```

After 30 seconds, show vibration > 0.30g:
```bash
curl http://localhost:8000/api/v1/readings/latest | python -m json.tool
```

### Part 4: Dashboard Tour (4 min)

Open http://localhost:3000

Demonstrate:
- Device selection
- Real-time updates (watch values change)
- Chart history
- Status badges

### Q&A

---

## 30-Minute Demo (Comprehensive)

### Part 1: Architecture Overview (5 min)

Walk through ARCHITECTURE.md diagram. Explain each component, especially:

- **ESP32 → Mosquitto** — edge devices publish to local broker
- **RPi Gateway** — subscribes to local broker, enriches payloads, buffers when offline, optionally bridges to cloud MQTT
- **Backend** — FastAPI with async SQLite, MQTT subscriber in background thread, EventBus fan-out to SSE
- **Dashboard** — React + Recharts consuming SSE stream

### Part 2: ESP32 Firmware (8 min)

Show firmware files:
```bash
ls -la firmware/esp32/
cat firmware/esp32/main.py
```

Explain:
- Sensor registry pattern
- Offline buffering
- MQTT client with reconnection

Show one driver:
```bash
cat firmware/esp32/drivers/dht22.py
```

### Part 3: Backend Deep Dive (7 min)

Show all backend components:
```bash
ls -la backend/
cat backend/main.py
cat backend/database.py
```

Show MQTT subscriber:
```bash
cat backend/mqtt_subscriber.py
```

Show EventBus (key to live streaming):
```bash
cat backend/event_bus.py
```

Show routers:
```bash
ls backend/routers/
cat backend/routers/stream.py
```

Test API thoroughly:
```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
curl http://localhost:8000/api/v1/devices | python -m json.tool
curl http://localhost:8000/api/v1/readings/latest | python -m json.tool
```

### Part 4: Dashboard Deep Dive (5 min)

Show dashboard source:
```bash
ls -la dashboard/src/
cat dashboard/src/App.jsx
cat dashboard/src/hooks/useSensorStream.js
```

Explain how `useSensorStream` connects to `/api/v1/stream` via `EventSource`.

### Part 5: Simulator Deep Dive (3 min)

Show simulator code:
```bash
cat firmware/simulator/simulator.py
```

Run with multiple devices:
```bash
python firmware/simulator/simulator.py --devices 3 --interval 2 --anomaly
```

### Part 6: RPi Gateway (2 min)

Show gateway files:
```bash
ls -la firmware/rpi_gateway/
cat firmware/rpi_gateway/gateway_config.yaml
cat firmware/rpi_gateway/gateway.py
```

Explain the gateway's role:
- Listens on `iot/{org}/{site}/#`
- Enriches with `_gw_ts`, `_gw_id`, `_gw_site`
- Buffers upstream messages when cloud is offline
- Exposes `/health` and `/devices` on port 8080
- Flushes buffer on reconnect

### Part 7: Tests (2 min)

Run the test suite:
```bash
pytest tests/ -v
```

Point out:
- 4 sensor driver tests
- 6 simulator model tests
- 5 API endpoint tests (health, devices, readings, latest, SSE stream)
- 8 MQTT schema validation tests

### Part 8: Full Demo with Anomaly (5 min)

Restart everything fresh:
```bash
docker-compose down
docker-compose up -d
python firmware/simulator/simulator.py --devices 2 --interval 2 --anomaly
```

Show in dashboard:
- Normal operation (first 30s)
- Anomaly appears (after 30s)

### Q&A with Deep Dives

---

## Troubleshooting Guide

| Issue | Solution |
|-------|----------|
| Backend won't start | Check `docker-compose logs backend` |
| No data in dashboard | Verify simulator is running |
| MQTT connection failed | Check mosquitto: `docker-compose logs mosquitto` |
| SSE stream empty | Check backend MQTT subscriber connected to broker |
| Port already in use | Stop other services or change ports in docker-compose.yml |

## Presentation Tips

1. **Have everything ready** - Start docker-compose before starting
2. **Keep simulator running** - Data makes the demo meaningful
3. **Use two terminals** - One for commands, one for logs
4. **Have API responses ready** - Pre-fetch to show during Q&A
5. **Test in advance** - Run through the full demo before presenting

## Audience-Specific Adaptations

### For Executives
- Focus on dashboard and business value
- Show real-time data flow
- Skip deep technical details

### For Engineers
- Show all source code
- Explain architecture decisions (EventBus, aiosqlite, thread-safe pub/sub)
- Discuss scaling patterns
- Walk through the gateway enrichment pipeline

### For Customers
- Emphasize reliability and offline handling
- Show easy setup
- Demonstrate anomaly detection
- Show buffering when upstream is unavailable
