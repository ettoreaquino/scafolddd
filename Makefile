# Backend Tutorial DDD Makefile
# Simple utility for running tests and development tasks
#
# Quick Test Reference:
#   make test-unit         - Fast unit tests (183 tests)
#   make test-integration  - Integration tests with mocked AWS (2 tests)  
#   make test-infrastructure - All infrastructure layer tests (17 tests)
#   make test              - All tests combined
#
# The output format uses hierarchical reporting with colored output
# and maintains consistency across all test types.

.PHONY: help clean test test-all test-unit test-integration test-e2e test-html test-parallel test-domain test-application test-infrastructure test-api test-slow test-coverage
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
	@echo "$(YELLOW)Test Commands:$(NC)"
	@echo "$(GREEN)test$(NC)              Run all tests (same as test-all)"
	@echo "$(GREEN)test-all$(NC)          Run all tests (unit + integration + e2e)"
	@echo "$(GREEN)test-unit$(NC)         Run only unit tests (fast, isolated)"
	@echo "$(GREEN)test-integration$(NC)  Run only integration tests (external deps)"
	@echo "$(GREEN)test-e2e$(NC)          Run only end-to-end tests (full system)"
	@echo ""
	@echo "$(YELLOW)Test by Layer:$(NC)"
	@echo "$(GREEN)test-domain$(NC)       Run only domain layer tests"
	@echo "$(GREEN)test-application$(NC)  Run only application layer tests"
	@echo "$(GREEN)test-infrastructure$(NC) Run only infrastructure layer tests"
	@echo "$(GREEN)test-api$(NC)          Run only API layer tests"
	@echo ""
	@echo "$(YELLOW)Test Options:$(NC)"
	@echo "$(GREEN)test-html$(NC)         Run tests and generate HTML report"
	@echo "$(GREEN)test-parallel$(NC)     Run tests in parallel (faster)"
	@echo "$(GREEN)test-slow$(NC)         Run only slow tests"
	@echo "$(GREEN)test-coverage$(NC)     Run tests with coverage report"
	@echo ""
	@echo "$(YELLOW)Utilities:$(NC)"
	@echo "$(GREEN)clean$(NC)              Clean up generated files"
	@echo "$(GREEN)help$(NC)               Show this help message"

test: test-all ## Run all tests (default)

test-all: ## Run all tests (unit + integration + e2e)
	@echo "$(BLUE)Running all tests...$(NC)"
	@echo "$(YELLOW)This includes unit, integration, and e2e tests$(NC)"
	poetry run pytest

test-unit: ## Run only unit tests (fast, isolated)
	@echo "$(BLUE)Running unit tests...$(NC)"
	@echo "$(YELLOW)Fast tests without external dependencies$(NC)"
	poetry run pytest -m "unit" || true

test-integration: ## Run only integration tests (external dependencies)
	@echo "$(BLUE)Running integration tests...$(NC)"
	@echo "$(YELLOW)Tests with external dependencies (mocked AWS services, etc.)$(NC)"
	poetry run pytest -m "integration" || true

test-e2e: ## Run only end-to-end tests (full system)
	@echo "$(BLUE)Running end-to-end tests...$(NC)"
	@echo "$(YELLOW)Full system tests (slowest)$(NC)"
	poetry run pytest -m "e2e" || true

test-domain: ## Run only domain layer tests
	@echo "$(BLUE)Running domain layer tests...$(NC)"
	poetry run pytest -m "domain" || true

test-application: ## Run only application layer tests
	@echo "$(BLUE)Running application layer tests...$(NC)"
	poetry run pytest -m "application" || true

test-infrastructure: ## Run only infrastructure layer tests
	@echo "$(BLUE)Running infrastructure layer tests...$(NC)"
	poetry run pytest -m "infrastructure" || true

test-api: ## Run only API layer tests
	@echo "$(BLUE)Running API layer tests...$(NC)"
	poetry run pytest -m "api" || true

test-html: ## Run tests and generate HTML report
	@echo "$(BLUE)Running tests with HTML report...$(NC)"
	poetry run pytest --html=reports/pytest-report.html --self-contained-html

test-parallel: ## Run tests in parallel (faster)
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	poetry run pytest -n auto

test-slow: ## Run only slow tests
	@echo "$(BLUE)Running slow tests...$(NC)"
	poetry run pytest -m "slow"

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
	@find . -type d -name "reports" -exec rm -rf {} + 2>/dev/null || true 