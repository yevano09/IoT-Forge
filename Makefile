.PHONY: run stop demo sim sim1000 test logs clean install-deps

run:
	docker-compose up -d
	@echo ""
	@echo "  Services starting..."
	@echo "  Dashboard : http://localhost:3000"
	@echo "  API docs  : http://localhost:8000/docs"
	@echo "  MQTT      : localhost:1883"
	@echo ""
	@echo "  Run 'make demo' in a second terminal to start the simulator."

stop:
	docker-compose down

demo:
	cd firmware/simulator && python3 simulator.py \
		--devices 3 --interval 2 --anomaly --broker localhost

sim:
	cd firmware/simulator && python3 simulator.py \
		--devices 5 --interval 5 --broker localhost

sim1000:
	cd firmware/simulator && python3 simulator.py \
		--devices 1000 --interval 1 --broker localhost

test:
	cd .. && pytest month1-edge-sense/tests/ -v

test-cov:
	cd .. && pytest month1-edge-sense/tests/ -v --tb=short \
		--cov=month1-edge-sense/backend --cov-report=term-missing

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	rm -f backend/edge_sense.db
	@echo "Cleaned."

install-deps:
	pip install -r backend/requirements.txt
	pip install -r firmware/simulator/requirements.txt
	pip install -r firmware/rpi_gateway/requirements.txt
