.PHONY: help build up down restart logs ps clean test dev prod

# Default target
help:
	@echo "Odoo 18 MCP Project Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make build        Build Docker images"
	@echo "  make up           Start all services in development mode"
	@echo "  make down         Stop all services"
	@echo "  make restart      Restart all services"
	@echo "  make logs         View logs from all services"
	@echo "  make ps           List running services"
	@echo "  make clean        Remove all containers, volumes, and images"
	@echo "  make test         Run tests"
	@echo "  make dev          Start development environment"
	@echo "  make prod         Start production environment"
	@echo ""

# Build Docker images
build:
	docker-compose build

# Start all services in development mode
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Restart all services
restart:
	docker-compose restart

# View logs from all services
logs:
	docker-compose logs -f

# List running services
ps:
	docker-compose ps

# Remove all containers, volumes, and images
clean:
	docker-compose down -v --rmi all

# Run tests
test:
	docker-compose run --rm test-runner

# Start development environment
dev:
	docker-compose up -d

# Start production environment
prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Create required directories
setup:
	mkdir -p logs exports tmp data generated_modules
	chmod -R 777 logs exports tmp data generated_modules
