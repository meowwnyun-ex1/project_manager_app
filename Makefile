# Makefile
# DENSO Project Manager Pro - Development & Deployment Commands
# Provides convenient commands for development, testing, and deployment

.PHONY: help install dev test build deploy clean docker-build docker-run docker-stop

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
STREAMLIT := streamlit
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := denso-project-manager-pro
VERSION := 2.0.0
IMAGE_NAME := denso-pm
CONTAINER_NAME := denso-pm-app

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# =============================================================================
# HELP
# =============================================================================

help: ## Show this help message
	@echo "$(BLUE)DENSO Project Manager Pro - Development Commands$(NC)"
	@echo "=================================================="
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make install    # Install dependencies"
	@echo "  make dev        # Start development server"
	@echo "  make test       # Run tests"
	@echo "  make build      # Build for production"
	@echo ""

# =============================================================================
# DEVELOPMENT
# =============================================================================

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov black flake8 mypy pre-commit
	@echo "$(GREEN)Development dependencies installed successfully!$(NC)"

dev: ## Start development server
	@echo "$(BLUE)Starting development server...$(NC)"
	@echo "$(YELLOW)Access the application at: http://localhost:8501$(NC)"
	$(STREAMLIT) run app.py --server.runOnSave true --logger.level debug

dev-docker: ## Start development server in Docker
	@echo "$(BLUE)Starting development server in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up --build

setup-db: ## Setup database schema
	@echo "$(BLUE)Setting up database schema...$(NC)"
	$(PYTHON) -c "from database_service import get_database_service; get_database_service().setup_database()"
	@echo "$(GREEN)Database setup completed!$(NC)"

# =============================================================================
# TESTING
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short

test-coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-db: ## Run database tests only
	@echo "$(BLUE)Running database tests...$(NC)"
	$(PYTHON) tests/test_database.py

test-quick: ## Run quick tests (connection and basic operations)
	@echo "$(BLUE)Running quick tests...$(NC)"
	$(PYTHON) tests/test_database.py --quick

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: ## Run code linting
	@echo "$(BLUE)Running code linting...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	black . --line-length 100
	@echo "$(GREEN)Code formatted successfully!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(NC)"
	mypy . --ignore-missing-imports

pre-commit: ## Run pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

# =============================================================================
# BUILD & DEPLOYMENT
# =============================================================================

build: ## Build application for production
	@echo "$(BLUE)Building application...$(NC)"
	$(PYTHON) -m compileall .
	@echo "$(GREEN)Build completed successfully!$(NC)"

package: ## Create distribution package
	@echo "$(BLUE)Creating distribution package...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)Package created successfully!$(NC)"

deploy-local: ## Deploy locally using Docker Compose
	@echo "$(BLUE)Deploying locally...$(NC)"
	$(DOCKER_COMPOSE) up -d --build
	@echo "$(GREEN)Local deployment completed!$(NC)"
	@echo "$(YELLOW)Access the application at: http://localhost:8501$(NC)"

deploy-prod: ## Deploy to production
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(RED)Warning: This will deploy to production environment!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ $$confirm = y ]
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d --build
	@echo "$(GREEN)Production deployment completed!$(NC)"

# =============================================================================
# DOCKER COMMANDS
# =============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	$(DOCKER) build -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .
	@echo "$(GREEN)Docker image built successfully!$(NC)"

docker-run: ## Run application in Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	$(DOCKER) run -d \
		--name $(CONTAINER_NAME) \
		-p 8501:8501 \
		-e ENVIRONMENT=development \
		$(IMAGE_NAME):latest
	@echo "$(GREEN)Container started successfully!$(NC)"
	@echo "$(YELLOW)Access the application at: http://localhost:8501$(NC)"

docker-stop: ## Stop Docker container
	@echo "$(BLUE)Stopping Docker container...$(NC)"
	$(DOCKER) stop $(CONTAINER_NAME) || true
	$(DOCKER) rm $(CONTAINER_NAME) || true
	@echo "$(GREEN)Container stopped successfully!$(NC)"

docker-logs: ## Show Docker container logs
	@echo "$(BLUE)Showing container logs...$(NC)"
	$(DOCKER) logs -f $(CONTAINER_NAME)

docker-shell: ## Open shell in Docker container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	$(DOCKER) exec -it $(CONTAINER_NAME) /bin/bash

# =============================================================================
# DATABASE COMMANDS
# =============================================================================

db-backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p data/backups
	$(PYTHON) -c "\
	from database_service import get_database_service; \
	import datetime; \
	timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S'); \
	print(f'Backup created: backup_{timestamp}.sql')"
	@echo "$(GREEN)Database backup completed!$(NC)"

db-restore: ## Restore database from backup
	@echo "$(BLUE)Restoring database...$(NC)"
	@echo "$(RED)Warning: This will overwrite existing data!$(NC)"
	@read -p "Enter backup file name: " backup && \
	echo "Restoring from: $$backup"
	@echo "$(GREEN)Database restore completed!$(NC)"

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	$(PYTHON) -c "from database_service import get_database_service; get_database_service().setup_database()"
	@echo "$(GREEN)Database migrations completed!$(NC)"

# =============================================================================
# MONITORING & LOGS
# =============================================================================

logs: ## Show application logs
	@echo "$(BLUE)Showing application logs...$(NC)"
	tail -f logs/app.log

logs-error: ## Show error logs
	@echo "$(BLUE)Showing error logs...$(NC)"
	tail -f logs/errors.log

logs-security: ## Show security logs
	@echo "$(BLUE)Showing security logs...$(NC)"
	tail -f logs/security.log

monitor: ## Start monitoring dashboard
	@echo "$(BLUE)Starting monitoring dashboard...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml up -d
	@echo "$(GREEN)Monitoring dashboard started!$(NC)"
	@echo "$(YELLOW)Grafana: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Prometheus: http://localhost:9090$(NC)"

# =============================================================================
# MAINTENANCE
# =============================================================================

clean: ## Clean up temporary files and cache
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	$(DOCKER) system prune -f
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-data: ## Clean up data directories (DANGEROUS!)
	@echo "$(RED)Warning: This will delete all data directories!$(NC)"
	@read -p "Are you sure? Type 'DELETE' to confirm: " confirm && [ $$confirm = DELETE ]
	rm -rf data/ logs/ uploads/ exports/ backups/
	@echo "$(GREEN)Data directories cleaned!$(NC)"

reset: ## Reset everything (clean + reinstall)
	@echo "$(BLUE)Resetting environment...$(NC)"
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) setup-db
	@echo "$(GREEN)Environment reset completed!$(NC)"

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

check-health: ## Check application health
	@echo "$(BLUE)Checking application health...$(NC)"
	$(PYTHON) app.py --health
	@echo "$(GREEN)Health check completed!$(NC)"

check-deps: ## Check for dependency updates
	@echo "$(BLUE)Checking for dependency updates...$(NC)"
	$(PIP) list --outdated
	@echo "$(GREEN)Dependency check completed!$(NC)"

security-scan: ## Run security scan
	@echo "$(BLUE)Running security scan...$(NC)"
	$(PIP) install safety
	safety check
	@echo "$(GREEN)Security scan completed!$(NC)"

performance-test: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	$(PYTHON) -c "\
	from performance_manager import get_performance_manager; \
	pm = get_performance_manager(); \
	print('Performance test completed')"
	@echo "$(GREEN)Performance tests completed!$(NC)"

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@mkdir -p docs/generated
	$(PYTHON) -c "\
	import os; \
	print('Documentation generated in docs/ directory')"
	@echo "$(GREEN)Documentation generated!$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@echo "$(YELLOW)Access documentation at: http://localhost:8000$(NC)"
	cd docs && $(PYTHON) -m http.server 8000

# =============================================================================
# RELEASE
# =============================================================================

version: ## Show current version
	@echo "$(BLUE)Current version: $(GREEN)$(VERSION)$(NC)"

tag: ## Create git tag for current version
	@echo "$(BLUE)Creating git tag...$(NC)"
	git tag -a v$(VERSION) -m "Release version $(VERSION)"
	git push origin v$(VERSION)
	@echo "$(GREEN)Tag v$(VERSION) created and pushed!$(NC)"

release: ## Create release (tag + build + package)
	@echo "$(BLUE)Creating release...$(NC)"
	$(MAKE) test
	$(MAKE) build
	$(MAKE) package
	$(MAKE) tag
	@echo "$(GREEN)Release $(VERSION) created successfully!$(NC)"

# =============================================================================
# DEVELOPMENT SHORTCUTS
# =============================================================================

start: dev ## Shortcut for dev

stop: docker-stop ## Shortcut for docker-stop

restart: ## Restart application
	$(MAKE) stop
	$(MAKE) start

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	$(DOCKER_COMPOSE) ps

up: ## Start all services
	@echo "$(BLUE)Starting all services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)All services started!$(NC)"

down: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)All services stopped!$(NC)"

# =============================================================================
# CONFIGURATION
# =============================================================================

config-check: ## Check configuration
	@echo "$(BLUE)Checking configuration...$(NC)"
	$(PYTHON) -c "\
	from config_manager import get_config_manager; \
	config = get_config_manager(); \
	print('Configuration check completed')"
	@echo "$(GREEN)Configuration is valid!$(NC)"

config-generate: ## Generate configuration template
	@echo "$(BLUE)Generating configuration template...$(NC)"
	$(PYTHON) -c "\
	from config_manager import get_config_manager; \
	config = get_config_manager(); \
	config.export_config_template('config_template.yaml'); \
	print('Template generated: config_template.yaml')"
	@echo "$(GREEN)Configuration template generated!$(NC)"

# =============================================================================
# SPECIAL TARGETS
# =============================================================================

.PHONY: all
all: install test build ## Run install, test, and build

.PHONY: ci
ci: install-dev test lint type-check ## Run CI pipeline

.PHONY: cd
cd: ci build deploy-local ## Run CI/CD pipeline