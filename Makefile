.PHONY: install clean run test lint kill-ports

# Python virtual environment
VENV = backend/venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Installation
install: install-backend install-frontend

install-backend:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

# Running services
run:
	@echo "Starting backend and frontend servers..."
	@make run-backend & make run-frontend

run-backend:
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload

run-frontend:
	cd frontend && npm start

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && source venv/bin/activate && pytest

test-frontend:
	cd frontend && npm test

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd backend && source venv/bin/activate && flake8

lint-frontend:
	cd frontend && npm run lint

# Kill processes on commonly used ports
kill-ports:
	@echo "Killing processes on ports 3000 (frontend) and 8000 (backend)..."
	-lsof -ti :3000 | xargs kill -9 2>/dev/null || true
	-lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Cleaning
clean: kill-ports
	rm -rf $(VENV)
	rm -rf frontend/node_modules
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	find . -type f -name ".DS_Store" -delete
