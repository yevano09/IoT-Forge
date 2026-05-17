# ============================================================
# CrewAI Tasks - Four week functions with detailed descriptions
# Each task: 100+ words description, expected_output, agent, context
# ============================================================

from crewai import Task
from agents import data_engineer, iot_engineer, frontend_developer, devops_engineer, project_manager


def week1_tasks():
    return [
        Task(
            description="Design the complete data architecture for the IoT platform including MQTT topic schema, database schema for sensor readings and device status, and API endpoints. The architecture must support high-throughput ingestion, efficient queries for dashboard visualization, and future scalability to 10,000+ devices. Consider data retention policies and partitioning strategies for time-series data.",
            expected_output="Complete data architecture document with MQTT topic patterns, database schema diagrams, API specification, and scalability recommendations",
            agent=data_engineer,
            context=[]
        ),
        Task(
            description="Implement the ESP32 firmware core components: local buffer for offline data persistence using btree or filesystem, MQTT client wrapper with TLS support and exponential backoff reconnection, and status reporter for heartbeat messages. The firmware must handle network disruptions gracefully, buffer up to 500 readings when offline, and automatically flush buffered data upon reconnection.",
            expected_output="Working ESP32 firmware modules for local_buffer.py, mqtt_client.py, and status_reporter.py with proper error handling and power-loss recovery",
            agent=iot_engineer,
            context=[]
        ),
        Task(
            description="Create a comprehensive project plan with weekly milestones, task assignments, risk assessment, and resource allocation for the 4-week development sprint. The plan should include specific deliverables, acceptance criteria, and checkpoints to ensure progress tracking and timely delivery.",
            expected_output="4-week project plan with detailed task breakdown, timeline, milestones, and resource allocation",
            agent=project_manager,
            context=[]
        )
    ]


def week2_tasks():
    return [
        Task(
            description="Develop and test all three sensor drivers (DHT22 for temperature/humidity, MPU6050 for vibration with gravity compensation, and generic ADC with oversampling) with proper error handling that returns quality=0 on hardware failures instead of raising exceptions. Each driver must be pluggable and registered via the sensor registry system.",
            expected_output="Three working sensor drivers (dht22.py, mpu6050.py, adc_generic.py) and sensor_registry.py for dynamic loading",
            agent=iot_engineer,
            context=[]
        ),
        Task(
            description="Build the RPi Gateway application that subscribes to the local MQTT broker, enriches incoming payloads with gateway metadata, buffers data when upstream broker is offline, and flushes buffer upon reconnection. The gateway must expose /health and /devices HTTP endpoints for health checks and device listing.",
            expected_output="Running RPi gateway with local and upstream MQTT forwarding, offline buffering, and HTTP health endpoints",
            agent=devops_engineer,
            context=[]
        ),
        Task(
            description="Implement the device simulator that can simulate multiple ESP32 devices, generate realistic sensor data based on sensor types, and support anomaly injection that makes vibration_rms exceed 0.30g after 30 seconds. The simulator must publish to MQTT with proper topic structure.",
            fully_autonomous=True,
            expected_output="Python simulator script that can run with --devices, --interval, and --anomaly flags to generate test data",
            agent=iot_engineer,
            context=[]
        )
    ]


def week3_tasks():
    return [
        Task(
            description="Develop the FastAPI backend with SQLite database, async MQTT subscriber that routes messages to the database and EventBus, REST API endpoints for devices and readings with filtering/pagination, and Server-Sent Events endpoint for real-time streaming with 30-second keepalive. Include health check endpoint and proper CORS configuration.",
            expected_output="Working FastAPI backend with database, MQTT subscriber, REST API, and SSE streaming endpoints",
            agent=data_engineer,
            context=[]
        ),
        Task(
            description="Build the React dashboard with SSE hook that maintains a rolling buffer of 100 readings per device-sensor combination, device list with status badges, gauge cards showing current values that gray out after 30 seconds, and Recharts line charts displaying the last 50 readings. The dashboard must filter by selected device.",
            expected_output="React dashboard with real-time data visualization, device management, and historical charts",
            agent=frontend_developer,
            context=[]
        ),
        Task(
            description="Create Docker infrastructure with three services: Mosquitto MQTT broker, backend API, and React dashboard served via nginx. Configure proper health checks, dependency ordering (backend waits for mosquitto), and networking between containers.",
            expected_output="docker-compose.yml and Dockerfile configurations for all three services with proper integration",
            agent=devops_engineer,
            context=[]
        )
    ]


def week4_tasks():
    return [
        Task(
            description="Write comprehensive test suite covering MQTT schema validation, sensor driver behavior with mocked hardware, API endpoint testing with httpx AsyncClient, and simulator output verification. Tests must cover offline buffering, data enrichment, and error handling paths.",
            expected_output="Test suite with tests for MQTT schema, sensor drivers, API endpoints, and simulator with >80% coverage",
            agent=data_engineer,
            context=[]
        ),
        Task(
            description="Create complete documentation including MQTT schema reference with all topic patterns and payload examples, architecture diagram showing data flow from sensors to dashboard, demo scripts for 5/15/30 minute sessions, and README with installation, usage, and troubleshooting sections.",
            expected_output="Complete documentation package: MQTT_SCHEMA.md, ARCHITECTURE.md, DEMO_SCRIPT.md, and README.md",
            agent=project_manager,
            context=[]
        ),
        Task(
            description="Final integration testing and verification: ensure simulator publishes data, backend receives and stores readings, dashboard displays real-time data, and all services start cleanly with docker-compose. Fix any integration issues and verify all quality gates.",
            expected_output="Verified working system with all components integrated and passing final validation checks",
            agent=devops_engineer,
            context=[]
        )
    ]