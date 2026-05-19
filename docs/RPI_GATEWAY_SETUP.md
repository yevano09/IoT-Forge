# RPi Gateway Setup Guide

Set up a Raspberry Pi as a local MQTT gateway that collects sensor data from ESP32 devices and forwards it to the IoT Forge backend.

## Hardware Requirements

| Item            | Recommended                     |
|-----------------|---------------------------------|
| Raspberry Pi    | 3B+ or 4B (2 GB+ RAM)          |
| SD Card         | 16 GB+ (32 GB recommended)      |
| Power Supply    | Official 5.1V USB-C (Pi 4)      |
| Network         | Ethernet or Wi-Fi               |

## 1. Install Raspberry Pi OS

Flash **Raspberry Pi OS Lite (64-bit, Bookworm)** using the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).

### Enable headless access (before first boot)

In the Imager settings:
- Hostname: `rpi-gateway`
- Enable SSH (public key or password)
- Set username/password
- Configure Wi-Fi (SSID + password)

### Connect via SSH

```bash
ssh pi@rpi-gateway.local   # or use the IP from your router
```

## 2. System Update & Tools

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git mosquitto mosquitto-clients
```

## 3. Install & Configure Mosquitto

Mosquitto runs the local MQTT broker that ESP32 devices connect to.

### Create config

```bash
sudo nano /etc/mosquitto/conf.d/local.conf
```

```ini
listener 1883 0.0.0.0
protocol mqtt

allow_anonymous true
```

### Restart and enable

```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

### Verify

```bash
mosquitto_sub -h localhost -t "test" -v &
mosquitto_pub -h localhost -t "test" -m "hello"
# you should see: test hello
kill %1
```

## 4. Clone the Project

```bash
cd ~
git clone https://github.com/<YOUR_ORG>/month1-edge-sense.git
cd month1-edge-sense
```

## 5. Install Gateway Dependencies

```bash
cd firmware/rpi_gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 6. Configure the Gateway

Edit `gateway_config.yaml`:

```yaml
gateway:
  id: "rpi-gw-001"              # unique gateway identifier
  org_id: "demo"                 # matches backend org
  site_id: "blr-demo"            # matches backend site

local_broker:
  host: "localhost"              # Mosquitto on the RPi
  port: 1883

upstream_broker:
  enabled: false                 # set true when cloud broker is ready
  host: "YOUR_CLOUD_BROKER_HOST"
  port: 8883
  username: ""
  password: ""

buffer_size: 10000
stats_interval_s: 30
api_port: 8080
```

### Key settings

- **gateway.id**: Unique name for this gateway (appears as `_gw_id` in enriched payloads)
- **local_broker**: Points to Mosquitto running on the RPi (port 1883)
- **upstream_broker**: Enable when bridging to a cloud MQTT broker (TLS on 8883)
- **buffer_size**: Max messages queued in memory when upstream is offline
- **api_port**: HTTP endpoint for `/health` and `/metrics`

## 7. Run the Gateway

### Manual start (for testing)

```bash
cd ~/month1-edge-sense/firmware/rpi_gateway
source venv/bin/activate
python gateway.py
```

Expected output:

```
12:34:56  INFO     gateway   Local subscribed  topic=iot/demo/blr-demo/#
12:34:56  INFO     gateway   Upstream broker disabled — local-only mode
12:34:56  INFO     gateway   Gateway API  http://0.0.0.0:8080/health
12:34:56  INFO     gateway   Gateway running — Ctrl+C to stop
```

### Verify it's collecting data

From another terminal, subscribe to see enriched messages:

```bash
mosquitto_sub -h localhost -t "iot/demo/blr-demo/#" -v
```

Then simulate an ESP32 message:

```bash
mosquitto_pub -h localhost -t "iot/demo/blr-demo/ESP32-001/temperature/raw" \
  -m '{"device_id":"ESP32-001","sensor":"temperature","value":25.5,"unit":"celsius","ts":'"$(date +%s)"'000,"seq":1}'
```

The gateway enriches the payload with `_gw_ts`, `_gw_id`, `_gw_site` and prints it:

```
iot/demo/blr-demo/ESP32-001/temperature/raw {"device_id":"ESP32-001","sensor":"temperature","value":25.5,...,"_gw_ts":...,"_gw_id":"rpi-gw-001","_gw_site":"blr-demo"}
```

## 8. Run as a Systemd Service

Create the service file:

```bash
sudo nano /etc/systemd/system/iot-gateway.service
```

```ini
[Unit]
Description=IoT Forge RPi Gateway
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/month1-edge-sense/firmware/rpi_gateway
ExecStart=/home/pi/month1-edge-sense/firmware/rpi_gateway/venv/bin/python gateway.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable iot-gateway
sudo systemctl start iot-gateway
```

Check status:

```bash
sudo systemctl status iot-gateway
```

Follow logs:

```bash
sudo journalctl -u iot-gateway -f
```

## 9. Monitoring Endpoints

The gateway exposes an HTTP API on port 8080:

| Endpoint    | Description                          |
|-------------|--------------------------------------|
| `/health`   | JSON: upstream status, device count  |
| `/devices`  | JSON: known devices with last_seen   |
| `/metrics`  | Prometheus format (8 metrics)        |

Test from the RPi:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/devices
curl http://localhost:8080/metrics
```

### Example /health response

```json
{
  "status": "ok",
  "upstream_connected": false,
  "known_devices": 1,
  "buffer_size": 0,
  "forwarded": 42,
  "buffered": 0
}
```

## 10. Connect to Your Backend

### Option A: Direct MQTT bridge (upstream broker)

Edit `gateway_config.yaml` and set:

```yaml
upstream_broker:
  enabled: true
  host: "YOUR_SERVER_IP"          # or cloud broker address
  port: 1883
  username: ""                    # if authentication is required
  password: ""
```

Restart the gateway:

```bash
sudo systemctl restart iot-gateway
```

The gateway bridges all messages from the local Mosquitto to the upstream broker in real time. When the upstream disconnects, messages are buffered in memory and flushed on reconnection.

### Option B: Run the full stack on the RPi

For a self-contained setup, deploy the entire Docker Compose stack on the RPi:

```bash
cd ~/month1-edge-sense
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker pi
# log out and back in, then:
docker compose up -d
```

This runs Mosquitto, Backend API, Prometheus, and Grafana all on the Pi. The RPi gateway then forwards `localhost → localhost` (in-memory).

## 11. Scrape Gateway Metrics with Prometheus

Add the RPi gateway as a scrape target in `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "rpi-gateway"
    static_configs:
      - targets: ["192.168.1.42:8080"]   # replace with your RPi IP
```

Reload Prometheus:

```bash
curl -X POST http://localhost:9090/-/reload
```

## 12. Troubleshooting

### Gateway won't connect to local Mosquitto

```bash
sudo systemctl status mosquitto
sudo journalctl -u mosquitto -f
```

### "Address already in use" on port 8080

Change `api_port` in `gateway_config.yaml` to a different value (e.g. 8081).

### ESP32 devices not showing up

- Verify the device publishes to `iot/{org}/{site}/{device_id}/...`
- Check the org and site IDs match between ESP32 config and gateway config
- Run `mosquitto_sub -h localhost -t "iot/#" -v` to see all incoming messages

### Messages buffered but not forwarded

Check the upstream broker config and network connectivity:

```bash
curl http://localhost:8080/health
```
Look for `"upstream_connected": false`.
