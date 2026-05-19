.PHONY: help build up down logs clean test install-simulator install-gateway install-backend install-dashboard

help:
	@echo "IoT Forge - Makefile Commands"
	@echo "================================"
	@echo "make build          - Build all Docker images"
	@echo "make up              - Start all services (incl. Prometheus + Grafana)"
	@echo "make down            - Stop all services"
	@echo "make logs            - Show logs from all services"
	@echo "make clean           - Remove containers, volumes, images"
	@echo "make test            - Run all tests"
	@echo "make install-backend - Install backend dependencies"
	@echo "make install-simulator - Install simulator dependencies"
	@echo "make install-gateway  - Install gateway dependencies"
	@echo "make health          - Check backend API health"
	@echo "make devices         - List known devices"
	@echo "make readings        - Show latest readings"
	@echo "make prometheus      - Open Prometheus web UI"
	@echo "make grafana         - Open Grafana web UI"

build:
	docker-compose build

up:
	docker-compose up -d --build
	@echo "Services started:"
	@echo "  - Mosquitto:  localhost:1883"
	@echo "  - Backend:   localhost:8000"
	@echo "  - Dashboard: localhost:3000"
	@echo "  - Prometheus: localhost:9090"
	@echo "  - Grafana:    localhost:3030 (admin/admin)"

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker rmi $$(docker images -q iot-forge-*) 2>/dev/null || true

test:
	cd tests && pip install -q pytest pytest-asyncio httpx && pytest -v

install-backend:
	pip install -r backend/requirements.txt

install-simulator:
	pip install -r firmware/simulator/requirements.txt

install-gateway:
	pip install -r firmware/rpi_gateway/requirements.txt

install-dashboard:
	cd dashboard && npm install

dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-dashboard:
	cd dashboard && npm run dev

simulator:
	python firmware/simulator/simulator.py --devices 3 --interval 2 --anomaly

gateway:
	python firmware/rpi_gateway/gateway.py firmware/rpi_gateway/gateway_config.yaml

health:
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool

devices:
	@curl -s http://localhost:8000/api/v1/devices | python -m json.tool

readings:
	@curl -s http://localhost:8000/api/v1/readings/latest | python -m json.tool

prometheus:
	@echo "Opening Prometheus web UI at http://localhost:9090"
	@start http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 2>/dev/null || open http://localhost:9090

grafana:
	@echo "Opening Grafana web UI at http://localhost:3030 (admin/admin)"
	@start http://localhost:3030 2>/dev/null || xdg-open http://localhost:3030 2>/dev/null || open http://localhost:3030
