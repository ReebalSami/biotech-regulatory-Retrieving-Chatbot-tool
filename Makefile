.PHONY: install run-backend run-frontend run clean

# Variables
PYTHON = python3
VENV_DIR = backend/venv
BACKEND_DIR = backend
FRONTEND_DIR = frontend

# Install dependencies and set up virtual environment
install:
	# Create and activate virtual environment for backend
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && \
	pip install --upgrade pip && \
	cd $(BACKEND_DIR) && \
	pip install -r requirements.txt
	# Install frontend dependencies
	cd $(FRONTEND_DIR) && npm install

# Run backend server
run-backend:
	. $(VENV_DIR)/bin/activate && \
	cd $(BACKEND_DIR) && \
	python -m uvicorn app.main:app --reload

# Run frontend server
run-frontend:
	cd $(FRONTEND_DIR) && npm start

# Run both servers (in separate terminals)
run:
	@echo "Starting backend and frontend servers..."
	@make run-backend & make run-frontend

# Clean up generated files and virtual environment
clean:
	rm -rf $(VENV_DIR)
	cd $(FRONTEND_DIR) && rm -rf node_modules
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
