.PHONY: help install run test migrate upgrade downgrade init-db import-test-codes docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make init-db          - Initialize database and run migrations"
	@echo "  make import-test-codes - Import test promo codes"
	@echo "  make run              - Run the bot"
	@echo "  make migrate MSG=...  - Create new migration"
	@echo "  make upgrade          - Apply migrations"
	@echo "  make downgrade        - Rollback last migration"
	@echo "  make docker-up        - Start PostgreSQL in Docker"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make clean            - Clean cache files"

install:
	pip install -r requirements.txt

init-db:
	alembic upgrade head

import-test-codes:
	python -m tools.import_codes --test

run:
	python -m app.main

migrate:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make migrate MSG='your message'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(MSG)"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

docker-up:
	docker-compose up -d postgres

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
