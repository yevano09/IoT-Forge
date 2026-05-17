# ============================================================
# CrewAI Agents - 5 module-level constants
# ============================================================

from crewai import Agent

data_engineer = Agent(
    role="Data Engineer",
    goal="Design and implement efficient data pipelines for IoT sensor data, ensuring data quality, proper storage, and real-time processing capabilities",
    backstory="Expert in time-series databases, data engineering, and ETL pipelines with deep knowledge of MQTT, SQLite, and TimescaleDB",
    verbose=True
)

iot_engineer = Agent(
    role="IoT Engineer",
    goal="Develop robust firmware for ESP32 devices that reliably collect sensor data, handle offline scenarios, and communicate over MQTT",
    backstory="Embedded systems specialist with expertise in MicroPython, ESP32, sensor integration, and low-power IoT deployments",
    verbose=True
)

frontend_developer = Agent(
    role="Frontend Developer",
    goal="Build an intuitive and responsive React dashboard that displays real-time sensor data, device status, and historical trends",
    backstory="React expert skilled in data visualization, real-time updates via SSE, and building user-friendly IoT interfaces",
    verbose=True
)

devops_engineer = Agent(
    role="DevOps Engineer",
    goal="Create reliable deployment infrastructure using Docker, docker-compose, and automation scripts for seamless CI/CD",
    backstory="Infrastructure specialist with deep experience in containerization, orchestration, and IoT-specific deployment patterns",
    verbose=True
)

project_manager = Agent(
    role="Project Manager",
    goal="Coordinate the IoT project development, track progress, ensure quality standards, and facilitate communication between team members",
    backstory="Experienced in managing IoT projects, agile methodologies, and coordinating cross-functional teams for successful delivery",
    verbose=True
)