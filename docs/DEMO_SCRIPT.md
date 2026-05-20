# IoT Forge — Edge Sense Demo Script

## Setup checklist (do this before every meeting)

- [ ] Laptop charged and plugged in
- [ ] Docker Desktop (or Docker Engine) running
- [ ] Project cloned and terminal open at `month1-edge-sense/`
- [ ] No leftover containers: `docker-compose down -v`
- [ ] All ports free: `lsof -i :1883 :8000 :3000` (or `netstat -an` on Windows)
- [ ] Services started: `docker-compose up -d` and `docker-compose ps` shows all healthy
- [ ] Simulator NOT yet running (save it for the demo moment)
- [ ] Browser tab open at http://localhost:3000 (dashboard) and http://localhost:8000/docs (API)
- [ ] Backup hotspot / tethering ready in case venue Wi-Fi is slow
- [ ] Demo tested end-to-end 30 minutes before the meeting

---

## Demo A — 5 minutes (investor hallway / first contact)

**Audience**: Anyone with 5 minutes. Investor, potential customer, accelerator judge.

**Opening hook** (say this exact sentence to open):

"I'm going to show you something that took a team of five engineers six months to build — and I built it in one month, solo, with AI agents writing most of the code."

**Step 1 — show the dashboard** (~60 seconds)

Turn your laptop toward them and open http://localhost:3000.

"As you can see, the dashboard is live. On the left you see all the devices that are currently connected to the platform. On the right, you see five sensor readings updating in real time — temperature, humidity, vibration, peak vibration, and motor current."

Point at the gauge cards as you name each one.

"Each gauge card shows you the most recent value, how long ago it was received, and whether the reading is healthy or out of range. Green dot means good data. Red means the sensor is in alarm territory."

"Below the device list you will see the gateway panel — it tells us the upstream connection status, how many messages have been forwarded, and whether the message buffer is empty. All green, all healthy."

**Step 2 — trigger the anomaly** (~90 seconds)

Turn to your second terminal and run:

```bash
cd month1-edge-sense
python firmware/simulator/simulator.py --devices 3 --interval 2 --anomaly
```

"Right now we're running three simulated factory devices. Each one publishes five sensor readings every two seconds over MQTT. Watch what happens after about thirty seconds."

Wait for the anomaly to trigger (30 seconds). Point at the vibration gauge.

"There. The vibration RMS just spiked. In a real factory, this is what a bearing failure looks like twenty minutes before it happens. The anomaly injector simulates a sudden vibration increase — exactly what you would see from a misaligned shaft or a failing bearing."

"This answers the question every plant manager asks: can this system detect trouble before it stops production? The answer is yes, and we can prove it."

**Step 3 — show the alert** (~60 seconds)

Point at the dashboard.

"Notice the gauge colour changed from green to amber to red as the value climbed. The dashboard is showing you, in real time, that something is wrong. You don't need a data scientist to read this. A floor supervisor can look at this screen and know immediately which machine needs attention."

"The Prometheus alerting system behind this would fire a notification within fifteen seconds of the spike. In Month 2, that notification goes to WhatsApp and email."

**Closing line** (say this to end the 5-min demo):

"What you just saw is a complete, production-grade IoT platform — running on a laptop — in under five minutes. It scales from one sensor to ten thousand with config changes, not code rewrites. I'd love to show you what it looks like under the hood."

**Top 3 questions they will ask + exact answers:**

1. **Q: "How long did this take you to build?"**
   **A:** "The core platform took four weeks. The firmware, the simulator, the RPi gateway, the backend API with five REST endpoints and a real-time event stream, a Prometheus and Grafana monitoring stack, and the React dashboard you just saw. Every component was written with AI agents — I did the architecture and the code review."

2. **Q: "What does this cost?"**
   **A:** "The software is open source. The hardware cost per device is about fifteen dollars for an ESP32 and a few sensors. For a full factory deployment, you add a Raspberry Pi per site — about fifty dollars — and a cloud server at roughly twenty dollars per month. That is the entire bill of materials."

3. **Q: "Can it work with our existing machines?"**
   **A:** "If your machine has a sensor output — 4-20 milliamp loop, Modbus, I2C, SPI, or even just a voltage signal — we can read it. The firmware has a pluggable driver system. Adding a new sensor type is one Python file and one line of configuration. I can show you that in under fifteen minutes."

---

## Demo B — 15 minutes (factory plant manager / operations team)

**Audience**: Non-technical. Cares about: downtime cost, ease of installation, reliability, alerts that actually work.

**Opening hook**:

"A factory in Coimbatore reduced unplanned downtime by thirty percent using exactly this kind of system. I want to show you how it works — and you can tell me whether it fits your machines."

**Step 1 — walking in and starting the demo** (1 minute)

Open the laptop, run the services, and pull up the dashboard.

"Let me start by showing you the complete system, end to end. This takes about twenty seconds to start."

```bash
docker-compose up -d
```

"I have a terminal open here. The dashboard is loading at localhost:3000. And I have the simulator ready to go."

**Step 2 — what the device list shows them** (2 minutes)

Point at the device list sidebar on the left.

"This is the device list. Every sensor node that is connected to the platform appears here. You can see the device ID, whether it is online or offline, the firmware version it is running, and when it last checked in."

"Online devices are shown at the top. Offline devices are collapsed under an accordion at the bottom — click it to expand and see which machines have dropped off. This is useful when you have hundreds of devices: the online ones are what matter right now, and the offline section helps you track which machines need attention."

"Right now there are no devices because the simulator hasn't started yet. Let me start it."

Run the simulator:

```bash
python firmware/simulator/simulator.py --devices 3 --interval 2
```

"Watch the device list. Within five seconds you will see three devices appear. Each one represents a real sensor node."

**Step 3 — live sensor readings — explain what each sensor means** (3 minutes)

Point at the gauge cards that appear.

"Each device publishes five sensor readings: temperature, humidity, vibration RMS, peak vibration, and motor current."

"Temperature and humidity are self-explanatory — they tell you the ambient conditions around the machine. If a motor is overheating, you see it here first."

"Vibration is the one I want you to pay attention to. Vibration analysis is how you predict bearing failures, shaft misalignment, and imbalance. In a traditional factory, you would have a technician walk the floor with a handheld vibration meter once a week. This system measures vibration continuously, every two seconds, on every machine."

"Motor current tells you if the machine is drawing more power than it should. A current spike can mean a mechanical bind, a failing motor, or a tool that needs replacement."

**Step 4 — trigger the anomaly** (3 minutes)

"This is the part that matters most."

Let the simulator run for 30 seconds. Then point at the vibration gauge.

"Watch the vibration gauge on the dashboard. In a few seconds it is going to spike."

(Wait for the anomaly to trigger.)

"There. That is what a bearing failure looks like twenty minutes before it happens. The vibration RMS value just climbed from below zero point one G to over zero point four G. In a real factory, that is the difference between a scheduled bearing replacement and a catastrophic shaft failure that stops production for three days."

"What you just witnessed is the system detecting the failure signature before the failure occurs. The dashboard changed colour from green to amber to red as the value climbed. Anyone looking at this screen — a floor supervisor, a maintenance manager, even a plant director — can see immediately that something is wrong."

**Step 5 — the alert arriving** (2 minutes)

"This is where the automation kicks in."

"Behind this dashboard, Prometheus is monitoring every sensor reading. When the vibration value crosses the high threshold, Prometheus fires an alert. In the production version, that alert goes to WhatsApp, email, and Slack simultaneously."

"For today's demo, I can show you the alert in the Prometheus console."

Open http://localhost:9090/alerts.

"Here are the active alerts. You can see 'HighVibration' is firing. The system detected the anomaly, evaluated it against the alerting rule, and raised an alarm — all within fifteen seconds of the reading arriving."

**Step 6 — adding a new sensor** (2 minutes)

"Here is the part your engineering team will appreciate."

"Adding a new sensor type to this platform takes exactly three steps. Let me show you."

Open `firmware/esp32/config.json`.

"Step one: create a driver file. Here is the existing driver for the DHT22 temperature and humidity sensor. It is about forty lines of Python."

"Step two: add one entry to the configuration file. I add the sensor name, the driver module, and the pin assignment."

"Step three: restart the device. That is it. The firmware loads the driver at boot time and starts publishing readings automatically."

"The simulator works the same way. If I add a new sensor type to the configuration, the simulated devices start publishing it. The backend stores it. The dashboard displays it. No code changes anywhere except the driver file and the config."

**Step 6a — gateway panel** (2 minutes)

"At the bottom of the sidebar there is a gateway panel. This shows you the health of the Raspberry Pi gateway that bridges this factory's local network to the cloud."

Point at the gateway panel.

"Upstream is showing Connected — that means the gateway has a live MQTT connection to the cloud broker. If the internet goes down, it switches to buffered mode automatically and stores up to ten thousand messages."

"The forwarded count shows how many sensor readings have been sent to the cloud since the gateway started. The buffer count is zero — meaning everything has been delivered. In a real deployment you can look at this panel and know immediately whether your data pipeline is healthy."

**Step 7 — leaving behind** (2 minutes)

"What I have shown you today is a platform that can monitor every machine in your factory for less than fifty dollars per site in hardware. It detects failures before they happen. It alerts your team automatically. And it is open source — you own the code, you control the data."

"I will leave you with a GitHub link, a one-page summary, and my contact information. I would love to set up a proof of concept on one of your machines. Pick the most critical machine on your floor, and we can have a sensor on it within a week."

**Top 5 questions + exact answers:**

1. **Q: "How long does installation take?"**
   **A:** "For the first machine, plan on a day. We install the sensor, configure the gateway, and verify the data flow. Every machine after that takes about thirty minutes. The software is already running — we are just adding sensors."

2. **Q: "Does installation require downtime?"**
   **A:** "Zero downtime. The sensors are non-invasive. Temperature sensors attach to the surface. Vibration sensors mount with a stud or adhesive. The machine never stops."

3. **Q: "What connectivity does it need?"**
   **A:** "Each device needs Wi-Fi to reach the local gateway. The gateway needs internet to reach the cloud. If the internet goes down, the gateway buffers up to ten thousand messages in memory and forwards them when connectivity returns. You lose nothing."

4. **Q: "What is the price per machine?"**
   **A:** "The hardware for one sensor node is approximately fifteen dollars for the ESP32 and the sensors. The gateway is a fifty-dollar Raspberry Pi. Cloud hosting is about twenty dollars per month. There is no per-device license fee."

5. **Q: "Who monitors the alerts?"**
   **A:** "Your existing maintenance team uses the same phone they already carry. Alerts go to WhatsApp or SMS. No new software to install, no new login to remember."

---

## Demo C — 30 minutes (CTO / technical deep-dive)

**Audience**: Technical decision-maker. Cares about: architecture, scalability, security, how to integrate with their existing stack, how it is built.

**Opening hook**:

"I want to show you the platform and then open the architecture — because the interesting story isn't just what it does, it is how it is built to scale."

**Step 1 — live dashboard walkthrough** (3 minutes)

Start the full stack and the simulator. Walk through every element of the dashboard.

"Let me start the complete stack."

```bash
docker-compose up -d
sleep 15
python firmware/simulator/simulator.py --devices 5 --interval 2 --anomaly
```

"The dashboard is at localhost:3000. Five simulated devices, each publishing five sensor readings every two seconds. The left sidebar shows every device with its online or offline status. Offline devices are tucked under a collapsible accordion — useful when you have hundreds of devices spread across a factory floor."

"Below the device list is the gateway panel. It shows the MQTT bridge status between the local Mosquitto and the upstream cloud broker. Right now it says upstream connected, three known devices, and over three thousand messages forwarded with zero buffered."

"The gauge cards at the top show the most recent value for each sensor type. Below that, each device plus sensor combination gets its own time-series chart."

"The data is streaming in via Server-Sent Events. The dashboard opens a single HTTP connection to the backend and receives every new reading as it arrives. No polling, no WebSockets, no extra infrastructure."

"But there is more happening behind the scenes. Every reading that passes through the gateway gets enriched with three additional fields: a gateway timestamp, a gateway ID, and a site identifier. This is how the cloud knows exactly which physical gateway forwarded which reading, and when it did it — critical for audit trails and latency monitoring."

**Step 2 — anomaly injection and detection** (4 minutes)

Wait for the anomaly to trigger.

"There. Vibration just spiked. The anomaly is injected at the simulator level — it simulates a mechanical failure by increasing the vibration reading by a factor of about five."

"The dashboard detected the anomaly purely through the data stream. No client-side logic needed. The Prometheus alerting rules behind this are even faster."

Open Prometheus at http://localhost:9090/alerts.

"The alert 'HighVibration' is now firing. The rule checks if vibration RMS exceeds zero point three G for more than fifteen seconds. When it does, the alert transitions from pending to firing."

"In production, Prometheus forwards this to Alertmanager, which handles deduplication, silencing, and routing to WhatsApp, Slack, email, or PagerDuty."

**Step 3 — MQTT topic stream in real time** (3 minutes)

Open a terminal and run:

```bash
mosquitto_sub -h localhost -t "iot/#" -v
```

"What you are seeing is the raw MQTT message stream. Every reading from every device, in real time."

Point out the topic structure:

"You can see the topic follows a strict schema: iq forward slash org ID, site ID, device ID, sensor type, and either 'raw' or 'status'."

"The payload is JSON with every field you need for a production system — device ID, organisation, site, sensor type, value, unit, quality flag, timestamp in milliseconds, sequence number, and firmware version."

"You will also notice the `_gw_ts`, `_gw_id`, and `_gw_site` fields on every message. Those are added by the gateway. A Raspberry Pi sitting on the factory floor receives the raw sensor readings over Wi-Fi, enriches them with gateway metadata, and forwards them upstream. If the internet is down, it buffers up to ten thousand messages in memory and replays them when connectivity returns."

"Let me show you the gateway's health endpoint to see this in action."

Run:
```bash
curl http://localhost:3000/gw/health
```

"Three thousand messages forwarded, zero in the buffer, upstream connected — the pipeline is healthy."

**Step 4 — OpenAPI spec** (3 minutes)

Open http://localhost:8000/docs.

"FastAPI generates this documentation automatically. Every endpoint is documented, with request and response schemas, and you can test each one directly from the browser."

Walk through the five API endpoints: health, devices list, readings, latest readings, SSE stream.

Demonstrate the SSE endpoint:

```bash
timeout 10 curl -N http://localhost:8000/api/v1/stream
```

"You can see the server-sent events arriving as JSON payloads. Each event is one sensor reading. The client opens this connection and receives events until it disconnects."

**Step 5 — pluggable architecture** (4 minutes)

"This is the part I think you will find most interesting. The architecture is designed so that every component is swappable without code changes."

Open `firmware/esp32/config.json` and a driver file.

"There is the driver interface. Every sensor driver implements a read method that returns a list of readings. Each reading has a sensor name, a value, a unit, and a quality flag."

"To add a new sensor, I write one file implementing this interface and add one entry to the configuration file. The firmware loads it dynamically at boot time."

"The same pattern applies at every layer. The backend database can switch from SQLite to PostgreSQL or TimescaleDB with one environment variable. The MQTT broker can switch from Mosquitto to EMQX with one config change."

**Step 6 — the scale path** (3 minutes)

Show the scaling table from the README.

"Let me talk about how this scales. On your laptop today, it runs on SQLite and Mosquitto. That handles about a hundred devices comfortably."

"For ten thousand devices, you change the broker from Mosquitto to EMQX. You change the database from SQLite to TimescaleDB. You add Kafka between the broker and the backend for buffer resilience. And you deploy Kubernetes for container orchestration."

"Every one of those changes is a configuration swap or an environment variable change. No code rewrites. The same MQTT topic schema, the same API endpoints, the same dashboard — just swapped out infrastructure underneath."

**Step 7 — CrewAI agent workflow** (5 minutes)

"This is how I built this in one month instead of six."

Open the CrewAI crew configuration.

"I use AI agents for code generation and task planning. The crew.py file defines four agents: a project manager, an architect, a senior developer, and a QA engineer."

"The agents plan the work, generate the code, review each other's output, and produce a completion summary. I review everything they produce and make the architectural decisions."

"For this project, the agents generated approximately eighty percent of the code. I handled the architecture, the integration testing, and the deployment configuration."

"You can see the task plan in crew.txt. Every task has a description, an assigned agent, a context from previous tasks, and expected deliverables."

**Step 8 — future months overview** (3 minutes)

"Month 1 is shipping today. Here is what is coming."

"Month 2, Fleet Commander, adds OTA firmware updates, remote configuration push, and a device registry with health monitoring."

"Month 3 adds AI: predictive maintenance models trained on the data you are already collecting, with CrewAI agents generating maintenance reports."

"Month 4 adds a multi-tenant web portal so you can manage multiple factories from a single dashboard."

"Month 5 adds edge ML — running inference on the ESP32 itself so the device can detect anomalies even when the network is down."

"Month 6 is production hardening: penetration testing, performance benchmarks, and SOC2 documentation."

**Step 9 — Q&A** (5 minute buffer)

**Top 5 questions + exact answers:**

1. **Q: "How is multi-tenancy handled?"**
   **A:** "Multi-tenancy is built into the data model. Every device has an org ID and a site ID. The API filters by these fields. In Month 4 we add role-based access control and isolated data views per organisation."

2. **Q: "Who owns the data?"**
   **A:** "You do. The entire platform is open source. You run it on your infrastructure. No data ever leaves your network unless you configure the upstream bridge to send it to a cloud endpoint you control."

3. **Q: "How secure is the OTA update process?"**
   **A:** "Firmware images are signed with ECDSA. The device verifies the signature before applying the update. The update channel uses TLS. Rollback is supported — if the new firmware crashes, the device reverts to the previous version."

4. **Q: "What is your CI/CD pipeline?"**
   **A:** "GitHub Actions runs linting, type checking, and the full test suite on every push. Docker images are built and pushed to a registry. The dashboard is deployed to Vercel for preview deployments. Everything is automated."

5. **Q: "How can we contribute or integrate?"**
   **A:** "The repo is public. Issues and pull requests are welcome. For integration, we have documented REST APIs and an MQTT schema. If you need a custom driver or a specific protocol adapter, we can build it in under a week."

---

## Simulator commands (exact — copy-paste ready)

### Demo mode (3 devices, anomaly after 30s)
```bash
cd month1-edge-sense
python firmware/simulator/simulator.py \
  --devices 3 --interval 2 --anomaly --broker localhost
```

### Development mode (5 devices, no anomaly)
```bash
python firmware/simulator/simulator.py \
  --devices 5 --interval 5 --broker localhost
```

### Load test (1000 devices)
```bash
python firmware/simulator/simulator.py \
  --devices 1000 --interval 1 --broker localhost
```

---

## What to leave behind after every demo

- GitHub repo URL (keep it public)
- This README: month1-edge-sense/README.md
- A 1-page PDF summary (create separately)
- Your contact: name, email, LinkedIn
