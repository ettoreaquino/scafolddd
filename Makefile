# Backend Tutorial DDD Makefile
# Simple utility for running milestone sanity checks

.PHONY: help milestone-part2 milestone-all clean
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
	@echo "$(GREEN)milestone-part2$(NC)    Run Part 2: Domain Layer verification"
	@echo "$(GREEN)milestone-all$(NC)      Run all available milestone verifications"
	@echo "$(GREEN)clean$(NC)              Clean up generated files"
	@echo "$(GREEN)help$(NC)               Show this help message"

milestone-part2: ## Verify Part 2: Domain Layer Implementation
	@echo "$(BLUE)Running Part 2: Domain Layer Verification...$(NC)"
	@PYTHONPATH=. $(PYTHON) milestones/milestone_part2_domain_layer.py

milestone-part3: ## Verify Part 3: Application Layer Implementation
	@echo "$(BLUE)Running Part 3: Application Layer Verification...$(NC)"
	@PYTHONPATH=. $(PYTHON) milestones/milestone_part3_application_layer.py

milestone-all: ## Run all available milestone verifications
	@echo "$(BLUE)Running Available Milestone Verifications...$(NC)"
	@echo "$(YELLOW)Currently available: Part 2 (Domain Layer)$(NC)"
	@echo ""
	@$(MAKE) milestone-part2
	@$(MAKE) milestone-part3
	@echo ""
	@echo "$(GREEN)✅ All available milestone verifications completed!$(NC)"

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true 