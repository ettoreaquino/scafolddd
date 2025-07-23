# Backend Tutorial DDD Makefile
# Simple utility for running tests and development tasks

.PHONY: help clean test test-html test-parallel test-unit test-domain test-slow test-coverage
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[32m
BLUE := \033[34m
YELLOW := \033[33m
NC := \033[0m # No Color

# Python executable
PYTHON := python3

help: ## Show available commands
	@echo "$(BLUE)Backend Tutorial DDD - Available Commands$(NC)"
	@echo "========================================"
	@echo ""
	@echo "$(GREEN)test$(NC)              Run all tests with pytest"
	@echo "$(GREEN)test-html$(NC)         Run tests and generate HTML report"
	@echo "$(GREEN)test-parallel$(NC)     Run tests in parallel (faster)"
	@echo "$(GREEN)test-unit$(NC)         Run only unit tests"
	@echo "$(GREEN)test-domain$(NC)       Run only domain layer tests"
	@echo "$(GREEN)test-slow$(NC)         Run only slow tests"
	@echo "$(GREEN)test-coverage$(NC)     Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)clean$(NC)              Clean up generated files"
	@echo "$(GREEN)help$(NC)               Show this help message"

test: ## Run all tests with pytest
	@echo "$(BLUE)Running all tests...$(NC)"
	poetry run pytest

test-html: ## Run tests and generate HTML report
	@echo "$(BLUE)Running tests with HTML report...$(NC)"
	poetry run pytest --html=reports/pytest-report.html --self-contained-html

test-parallel: ## Run tests in parallel (faster)
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	poetry run pytest -n auto

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	poetry run pytest -m unit

test-domain: ## Run only domain layer tests
	@echo "$(BLUE)Running domain layer tests...$(NC)"
	poetry run pytest -m domain

test-slow: ## Run only slow tests
	@echo "$(BLUE)Running slow tests...$(NC)"
	poetry run pytest -m slow

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	poetry run pytest --cov=src --cov-report=html:reports/coverage --cov-report=term-missing



clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true 