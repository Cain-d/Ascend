.PHONY: help install install-dev setup test lint format clean run-api run-frontend run-all

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  setup        Complete project setup (install + init db)"
	@echo "  test         Run test suite"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean up temporary files"
	@echo "  run-api      Start the API server"
	@echo "  run-frontend Start the frontend development server"
	@echo "  run-all      Start both API and frontend (requires tmux)"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Setup
setup: install-dev
	python init_db.py
	@echo "✅ Setup complete! Copy .env.example to .env and configure your settings."

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 app/ tests/
	mypy app/
	black --check app/ tests/
	isort --check-only app/ tests/

format:
	black app/ tests/
	isort app/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

# Development servers
run-api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd ascend-frontend && npm run dev

# Run both (requires tmux)
run-all:
	tmux new-session -d -s ascend-api 'make run-api'
	tmux new-session -d -s ascend-frontend 'make run-frontend'
	@echo "✅ Started API and frontend servers in tmux sessions"
	@echo "   API: tmux attach -t ascend-api"
	@echo "   Frontend: tmux attach -t ascend-frontend"

# Database operations
migrate:
	python run_migrations.py

reset-db:
	rm -f data/ascend.db
	python init_db.py