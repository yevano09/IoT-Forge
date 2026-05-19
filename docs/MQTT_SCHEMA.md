# IoT Forge — Platform MQTT Topic Schema v1.0

## Topic Hierarchy

```
iot/{org_id}/{site_id}/{device_id}/{sensor_type}/raw
iot/{org_id}/{site_id}/{device_id}/{sensor_type}/agg
iot/{org_id}/{site_id}/{device_id}/status
iot/{org_id}/{site_id}/{device_id}/cmd/{command}
iot/{org_id}/{site_id}/{device_id}/cmd/{command}/ack
iot/forge/ota/{device_id}/push
iot/forge/ota/{device_id}/ack
```

## Field Definitions

| Field       | Type   | Description                                    |
|-------------|--------|------------------------------------------------|
| org_id      | string | Organisation slug e.g. `acme`                  |
| site_id     | string | Physical site e.g. `blr-plant-1`              |
| device_id   | string | Unique device MAC or UUID                      |
| sensor_type | string | `temperature`, `humidity`, `vibration_rms`, `vibration_peak`, `current` |

## Payload — Raw Reading

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

**Fields:**
- `device_id`: Unique device identifier
- `org_id`: Organization identifier
- `site_id`: Site/location identifier
- `sensor`: Sensor type (temperature, humidity, vibration_rms, vibration_peak, current)
- `value`: Numeric sensor value
- `unit`: Unit of measurement (celsius, percent, g, amps)
- `quality`: Data quality flag (1=good, 0=error/no data)
- `ts`: Unix timestamp in milliseconds
- `seq`: Sequence number for deduplication
- `fw_version`: Firmware version string

## Payload — Device Status Heartbeat

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

**Fields:**
- `device_id`: Unique device identifier
- `status`: Device status (online, offline)
- `rssi`: WiFi signal strength in dBm
- `heap_free`: Available memory in bytes
- `uptime_s`: Device uptime in seconds
- `ts`: Unix timestamp in milliseconds
- `fw_version`: Firmware version string

## Payload — Command

```json
{
  "cmd": "set_interval",
  "params": { "interval_ms": 5000 },
  "cmd_id": "cmd-uuid-001",
  "issued_ts": 1716000000000
}
```

**Supported Commands:**
- `set_interval`: Change sensor reading interval
  - `params.interval_ms`: New interval in milliseconds
- `reboot`: Reboot the device
- `reset_config`: Reset configuration to defaults

## Payload — Command Acknowledgment

```json
{
  "cmd_id": "cmd-uuid-001",
  "status": "ok",
  "device_id": "ESP32-A1B2C3"
}
```

## Gateway Enrichment (RPi Gateway)

When the RPi Gateway forwards messages to the upstream broker or backend, it adds these fields to every payload:

```json
{
  "_gw_ts": 1716000000123,
  "_gw_id": "rpi-gw-001",
  "_gw_site": "blr-demo"
}
```

| Field       | Type    | Description                            |
|-------------|---------|----------------------------------------|
| `_gw_ts`    | integer | Gateway receive timestamp (Unix ms)    |
| `_gw_id`    | string  | Gateway device ID                      |
| `_gw_site`  | string  | Site ID from gateway config            |

The backend MQTT subscriber stores all fields as-is in the `readings` table under their respective column names.

## QoS Levels

| Topic pattern      | QoS | Retain |
|--------------------|-----|--------|
| `.../raw`          | 0   | false  |
| `.../status`       | 1   | true   |
| `.../cmd/...`      | 1   | false  |
| `.../cmd/.../ack`  | 1   | false  |
| `forge/ota/.../push`| 1   | false  |

## Backend MQTT Subscription

The backend's `MQTTSubscriber` subscribes to `iot/#` and routes messages by topic suffix:

| Topic contains | Action                                         |
|----------------|------------------------------------------------|
| `/status`      | `db.upsert_device(payload)` — upserts device   |
| `/raw`         | `db.insert_reading(payload)` + `bus.publish()` |

The `EventBus.publish()` fans out the reading to all connected SSE clients in real time.

## Scaling Note

At small scale: run Mosquitto locally.

At medium scale: swap to EMQX (1M concurrent connections).

At large scale: AWS IoT Core / GCP IoT Core — same topic schema, no firmware change needed.

Config key: `MQTT_BROKER_URL` in `config.yaml`.

## Topic Examples

```
# Temperature reading from device at site
iot/acme/blr-plant-1/ESP32-A1B2C3/temperature/raw

# Humidity reading
iot/acme/blr-plant-1/ESP32-A1B2C3/humidity/raw

# Vibration RMS
iot/acme/blr-plant-1/ESP32-A1B2C3/vibration_rms/raw

# Device heartbeat/status
iot/acme/blr-plant-1/ESP32-A1B2C3/status

# Command to device
iot/acme/blr-plant-1/ESP32-A1B2C3/cmd/set_interval

# Command acknowledgment
iot/acme/blr-plant-1/ESP32-A1B2C3/cmd/set_interval/ack
```
