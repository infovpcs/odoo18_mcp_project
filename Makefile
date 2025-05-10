.PHONY: help setup build up down restart logs ps clean test test-mcp test-agent test-utils test-export-import dev prod

# Default target
help:
	@echo "Odoo 18 MCP Project Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup        Set up required directories (logs, exports, tmp, data, generated_modules)"
	@echo "  make build        Build Docker images"
	@echo "  make up           Start all services in development mode"
	@echo "  make down         Stop all services"
	@echo "  make restart      Restart all services"
	@echo "  make logs         View logs from all services"
	@echo "  make ps           List running services"
	@echo "  make clean        Remove all containers, volumes, and images"
	@echo "  make test         Run all tests"
	@echo "  make test-mcp     Run MCP server tests"
	@echo "  make test-agent   Run Odoo code agent tests"
	@echo "  make test-utils   Run Odoo code agent utilities tests"
	@echo "  make test-export-import  Run export/import agent tests"
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

# Run all tests
test:
	docker-compose run --rm test-runner test all

# Run MCP server tests
test-mcp:
	docker-compose run --rm test-runner test mcp

# Run Odoo code agent tests
test-agent:
	docker-compose run --rm test-runner test agent

# Run Odoo code agent utilities tests
test-utils:
	docker-compose run --rm test-runner test utils

# Run export/import agent tests
test-export-import:
	docker-compose run --rm test-runner test export-import

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
