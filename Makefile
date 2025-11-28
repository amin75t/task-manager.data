.PHONY: help install dev run docker-build docker-up docker-down docker-logs docker-shell clean test lint format prod-deploy prod-up prod-down prod-logs

# Default target
help:
	@echo "Task Manager API - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make dev            - Run development server with auto-reload"
	@echo "  make run            - Run production server"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code with black"
	@echo ""
	@echo "Docker (Development):"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-up      - Start containers in background"
	@echo "  make docker-down    - Stop and remove containers"
	@echo "  make docker-logs    - View container logs"
	@echo "  make docker-shell   - Open shell in container"
	@echo "  make docker-restart - Restart containers"
	@echo ""
	@echo "Production Deployment:"
	@echo "  make prod-deploy    - Deploy to production (build and start)"
	@echo "  make prod-up        - Start production containers"
	@echo "  make prod-down      - Stop production containers"
	@echo "  make prod-logs      - View production logs"
	@echo "  make prod-restart   - Restart production containers"
	@echo "  make prod-status    - Check production container status"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Remove cache and temporary files"
	@echo "  make db-reset       - Reset database (delete SQLite file)"
	@echo "  make db-backup      - Backup database"
	@echo "  make env-copy       - Copy .env.example to .env"
	@echo "  make nginx-test     - Test Nginx configuration"
	@echo "  make nginx-reload   - Reload Nginx configuration"
	@echo ""

# Development
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

dev:
	@echo "Starting development server..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run:
	@echo "Starting production server..."
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker compose build

docker-up:
	@echo "Starting containers..."
	docker compose up -d
	@echo "Application running at http://localhost:8080"
	@echo "API docs available at http://localhost:8080/docs"

docker-down:
	@echo "Stopping containers..."
	docker compose down

docker-logs:
	@echo "Showing container logs..."
	docker compose logs -f

docker-shell:
	@echo "Opening shell in container..."
	docker compose exec app /bin/bash

docker-restart:
	@echo "Restarting containers..."
	docker compose restart

# Production deployment commands
prod-deploy:
	@echo "Deploying to production..."
	@echo "Building and starting containers with Nginx..."
	docker compose -f docker-compose.prod.yml up -d --build
	@echo ""
	@echo "✅ Production deployment complete!"
	@echo "🌐 Application available at: http://task.ziro-one.ir:8080"
	@echo "📚 API docs: http://task.ziro-one.ir:8080/docs"
	@echo "❤️  Health check: http://task.ziro-one.ir:8080/health"

prod-up:
	@echo "Starting production containers..."
	docker compose -f docker-compose.prod.yml up -d
	@echo "Production containers started!"

prod-down:
	@echo "Stopping production containers..."
	docker compose -f docker-compose.prod.yml down
	@echo "Production containers stopped!"

prod-logs:
	@echo "Showing production logs..."
	docker compose -f docker-compose.prod.yml logs -f

prod-restart:
	@echo "Restarting production containers..."
	docker compose -f docker-compose.prod.yml restart
	@echo "Production containers restarted!"

prod-status:
	@echo "Production container status:"
	docker compose -f docker-compose.prod.yml ps

# Testing and Quality
test:
	@echo "Running tests..."
	pytest -v

lint:
	@echo "Running linting..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

format:
	@echo "Formatting code..."
	black .

# Utilities
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

db-reset:
	@echo "Resetting database..."
	rm -f tasks.db
	rm -f data/tasks.db
	@echo "Database reset complete!"

db-backup:
	@echo "Backing up database..."
	@mkdir -p backups
	@if [ -f data/tasks.db ]; then \
		cp data/tasks.db backups/tasks.db.backup-$$(date +%Y%m%d-%H%M%S); \
		echo "✅ Database backed up to backups/ directory"; \
	else \
		echo "⚠️  No database found to backup"; \
	fi

env-copy:
	@echo "Copying .env.example to .env..."
	cp .env.example .env
	@echo "Please update .env with your configuration"

# Nginx utilities
nginx-test:
	@echo "Testing Nginx configuration..."
	docker exec task-manager-nginx-prod nginx -t || \
	docker exec task-manager-nginx nginx -t

nginx-reload:
	@echo "Reloading Nginx configuration..."
	docker exec task-manager-nginx-prod nginx -s reload || \
	docker exec task-manager-nginx nginx -s reload
	@echo "Nginx reloaded!"

# Quick start commands
quick-start: env-copy install dev

docker-quick-start: env-copy docker-build docker-up
