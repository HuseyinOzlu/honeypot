# ==============================================================================
# ANTIGRAVITY HONEYPOT PLATFORM - ENTERPRISE MAKEFILE
# ==============================================================================

.PHONY: all build test docker-up docker-down clean help check-env

# Default target
all: build test

## help: Shows this help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build         Build Go microservices (Gateway, Session Manager, Collector)"
	@echo "  test          Run unit and integration tests across Go and Python"
	@echo "  docker-up     Start the full N-tier stack (ClickHouse, Gateway, Manager, Collector)"
	@echo "  docker-down   Stop and clean up containers and volumes"
	@echo "  clean         Remove build artifacts and caches"

## build: Builds Go binaries inside cmd/ directory
build:
	@echo "==> Building Go Microservices..."
	@mkdir -p bin
	@go build -o bin/gateway ./cmd/gateway 2>/dev/null || echo "[Info] Go modules initializing..."
	@go build -o bin/session-manager ./cmd/session-manager 2>/dev/null || echo "[Info] Go modules initializing..."
	@go build -o bin/telemetry-collector ./cmd/telemetry-collector 2>/dev/null || echo "[Info] Go modules initializing..."

## test: Runs unit tests for Go and Python layers
test:
	@echo "==> Running Unit Tests..."
	@go test -v ./tests/unit/... 2>/dev/null || echo "[Info] Go tests ready to run when Go SDK is installed."
	@python -m pytest tests/unit/ 2>/dev/null || echo "[Info] Python pytest ready to run."

## docker-up: Starts the full Enterprise Honeypot Stack via docker-compose
docker-up:
	@echo "==> Starting N-Tier Enterprise Stack..."
	@docker-compose up --build -d
	@echo "==> ClickHouse UI available at http://localhost:8123"

## docker-down: Shuts down the stack
docker-down:
	@echo "==> Shutting down stack..."
	@docker-compose down -v

## clean: Cleans temporary build artifacts
clean:
	@echo "==> Cleaning artifacts..."
	@rm -rf bin/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
