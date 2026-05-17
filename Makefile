.PHONY: help build up down logs clean test install-simulator install-gateway install-backend install-dashboard

help:
	@echo "IoT Forge - Makefile Commands"
	@echo "================================"
	@echo "make build          - Build all Docker images"
	@echo "make up              - Start all services"
	@echo "make down            - Stop all services"
	@echo "make logs            - Show logs from all services"
	@echo "make clean           - Remove containers, volumes, images"
	@echo "make test            - Run all tests"
	@echo "make install-backend - Install backend dependencies"
	@echo "make install-simulator - Install simulator dependencies"
	@echo "make install-gateway  - Install gateway dependencies"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started:"
	@echo "  - Mosquitto:  localhost:1883"
	@echo "  - Backend:   localhost:8000"
	@echo "  - Dashboard: localhost:3000"

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