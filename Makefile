.PHONY: up down init test pipeline quality docs help

DB_HOST ?= localhost
DB_PORT ?= 5432
DB_NAME ?= care_analytics
DB_USER ?= care_analyst
DB_PASSWORD ?= care_analyst_local

help:
	@echo "Available commands:"
	@echo "  make up        - Start PostgreSQL via Docker Compose"
	@echo "  make down      - Stop PostgreSQL"
	@echo "  make init      - Initialize database schema"
	@echo "  make quality   - Run data quality checks"
	@echo "  make pipeline  - Run full ETL pipeline"
	@echo "  make test      - Run pytest tests"
	@echo "  make sql       - Connect to PostgreSQL"
	@echo "  make docs      -Generate docs directory check"

up:
	docker compose up -d

down:
	docker compose down

init:
	docker compose exec postgres psql -U $(DB_USER) -d $(DB_NAME) -f sql/01_create_schema.sql
	docker compose exec postgres psql -U $(DB_USER) -d $(DB_NAME) -f sql/02_analytics_views.sql

test:
	python3 -m pytest tests/ -v

pipeline:
	python3 -m src.pipeline

quality:
	python3 -m src.quality_checks --check-only

sql:
	docker compose exec postgres psql -U $(DB_USER) -d $(DB_NAME)

docs:
	@echo "Documentation available in docs/"
