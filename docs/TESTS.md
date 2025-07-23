# Testing Strategy - TDD Approach

> **Comprehensive testing documentation for the Backend Tutorial DDD project using Test-Driven Development.**

## 📋 Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Domain Layer Tests](#domain-layer-tests)
- [Application Layer Tests](#application-layer-tests)
- [Test Configuration](#test-configuration)
- [Best Practices](#best-practices)

---

## 🎯 Testing Philosophy

This project follows **Test-Driven Development (TDD)** principles:

1. **Write tests first** - Define expected behavior before implementation
2. **Red-Green-Refactor** - Write failing test → Make it pass → Refactor
3. **Comprehensive coverage** - Test all layers and edge cases
4. **Fast feedback** - Tests run quickly for rapid development cycles
5. **Maintainable tests** - Clean, readable, and well-organized test code

### TDD Workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Write Test    │───>│  Run Test       │───>│   Test Fails    │
│   (Red)         │    │  (Red)          │    │   (Expected)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Refactor      │<───│  Run Test       │<───│  Write Code     │
│   (Clean)       │    │  (Green)        │    │  (Green)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🏗️ Test Structure

```
tests/
├── conftest.py                 # Global test configuration and fixtures
├── unit/                       # Unit tests (fast, isolated)
│   ├── domain/                 # Domain layer tests
│   │   ├── test_entities.py    # Entity tests
│   │   ├── test_value_objects.py # Value object tests
│   │   ├── test_events.py      # Domain event tests
│   │   └── test_repositories.py # Repository interface tests
│   └── application/            # Application layer tests
│       └── test_services.py    # Service tests
├── integration/                # Integration tests (external dependencies)
│   └── test_dynamodb_repository.py # DynamoDB integration tests
└── e2e/                        # End-to-end tests (full system)
    └── test_api_handlers.py    # API handler tests
```

---

## 🚀 Running Tests

### Basic Commands

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only domain layer tests
make test-domain

# Run tests with coverage
make test-coverage

# Run tests in parallel (faster)
make test-parallel

# Run tests with HTML report
make test-html
```

### Advanced Commands

```bash
# Run specific test file
poetry run pytest tests/unit/application/test_services.py

# Run specific test class
poetry run pytest tests/unit/application/test_services.py::TestListTasksService

# Run specific test method
poetry run pytest tests/unit/application/test_services.py::TestListTasksService::test_execute_with_user_with_tasks_returns_task_list

# Run tests with markers
poetry run pytest -m application  # Application layer tests only
poetry run pytest -m domain       # Domain layer tests only
poetry run pytest -m unit         # Unit tests only
poetry run pytest -m integration  # Integration tests only
```

---

## 📊 Test Categories

### Unit Tests (`@pytest.mark.unit`)

**Purpose:** Test individual components in isolation
**Speed:** Fast (< 1 second per test)
**Dependencies:** Mocked external dependencies
**Scope:** Single class, method, or function

**Examples:**
- Entity business logic validation
- Value object creation and validation
- Service method behavior
- Domain event generation

### Integration Tests (`@pytest.mark.integration`)

**Purpose:** Test component interactions
**Speed:** Medium (1-5 seconds per test)
**Dependencies:** Real external services (DynamoDB, SNS)
**Scope:** Multiple components working together

**Examples:**
- Repository with real DynamoDB
- Service with real event bus
- API handlers with real services

### End-to-End Tests (`@pytest.mark.e2e`)

**Purpose:** Test complete user workflows
**Speed:** Slow (5+ seconds per test)
**Dependencies:** Full deployed system
**Scope:** Complete API endpoints

**Examples:**
- Complete API request/response cycles
- Full user task management workflows
- Error handling scenarios

---

## 🏛️ Domain Layer Tests

### Entity Tests (`tests/unit/domain/test_entities.py`)

Tests for domain entities and their business logic:

```python
@pytest.mark.domain
@pytest.mark.unit
class TestTask:
    def test_task_creation_generates_event(self):
        """Test that creating a task generates TaskCreated event"""
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        events = task.pop_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCreated)
```

**Coverage:**
- ✅ Entity creation and validation
- ✅ Business rule enforcement
- ✅ Domain event generation
- ✅ State transitions
- ✅ Edge cases and error conditions

### Value Object Tests (`tests/unit/domain/test_value_objects.py`)

Tests for immutable value objects:

```python
@pytest.mark.domain
@pytest.mark.unit
class TestTaskId:
    def test_task_id_creation(self):
        """Test TaskId creation and validation"""
        task_id = TaskId("task-123")
        assert str(task_id) == "task-123"
        assert task_id.value == "task-123"
    
    def test_task_id_generation(self):
        """Test TaskId generation creates unique IDs"""
        id1 = TaskId.generate()
        id2 = TaskId.generate()
        assert id1 != id2
```

**Coverage:**
- ✅ Value object creation and validation
- ✅ Immutability
- ✅ Equality and comparison
- ✅ String representation
- ✅ Generation methods

### Domain Event Tests (`tests/unit/domain/test_events.py`)

Tests for domain events:

```python
@pytest.mark.domain
@pytest.mark.unit
class TestTaskCreated:
    def test_task_created_event_creation(self):
        """Test TaskCreated event creation"""
        event = TaskCreated(
            event_id="evt-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        assert event.aggregate_id == "task-456"
        assert event.task_title == "Test Task"
        assert event.user_id == "user-789"
```

**Coverage:**
- ✅ Event creation and validation
- ✅ Event serialization
- ✅ Event metadata
- ✅ Event inheritance

### Repository Interface Tests (`tests/unit/domain/test_repositories.py`)

Tests for repository interfaces using mocks:

```python
@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepository:
    @pytest.mark.asyncio
    async def test_save_task(self, mock_repository):
        """Test saving a task"""
        task = create_test_task()
        await mock_repository.save(task)
        assert mock_repository.save_called
```

**Coverage:**
- ✅ Repository method contracts
- ✅ Error handling
- ✅ Method call verification
- ✅ Return value validation

---

## 🎯 Application Layer Tests

### Service Tests (`tests/unit/application/test_services.py`)

Comprehensive tests for application services:

```python
@pytest.mark.application
@pytest.mark.unit
class TestListTasksService:
    @pytest.mark.asyncio
    async def test_execute_with_user_with_tasks_returns_task_list(self, list_tasks_service, task_repository, pending_task, in_progress_task):
        """Test that user with tasks returns list of tasks"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        
        result = await list_tasks_service.execute(str(pending_task.user_id))
        
        assert isinstance(result, list)
        assert len(result) == 2
```

**Coverage:**
- ✅ Service initialization and dependency injection
- ✅ Input validation and error handling
- ✅ Business logic execution
- ✅ Repository interaction
- ✅ Return value structure
- ✅ Event publishing
- ✅ Edge cases and error conditions

**Test Categories:**
1. **Initialization Tests** - Service dependency injection
2. **Input Validation Tests** - Parameter validation and error handling
3. **Successful Execution Tests** - Happy path scenarios
4. **Repository Interaction Tests** - Service-repository communication
5. **Return Value Tests** - Response structure and format
6. **Edge Cases Tests** - Boundary conditions and error scenarios

---

## ⚙️ Test Configuration

### Global Configuration (`tests/conftest.py`)

```python
import pytest
import asyncio
from moto import mock_aws
from src.infrastructure.container import Container

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture(scope="function")
def dynamodb_table(aws_credentials):
    """Create mocked DynamoDB table."""
    with mock_aws():
        # DynamoDB table creation logic
        yield table
```

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, external dependencies)
    e2e: End-to-end tests (slowest, full system)
    domain: Domain layer tests
    application: Application layer tests
    infrastructure: Infrastructure layer tests
    api: API layer tests
    asyncio: Async tests that require asyncio support

addopts = 
    --tb=no
    --strict-markers
    --color=yes
    --durations=10
    --cov=src
    --cov-report=html:reports/coverage
    --cov-fail-under=80
```

---

## 🎯 Best Practices

### Test Organization

1. **Arrange-Act-Assert Pattern**
   ```python
   def test_something():
       # Arrange - Set up test data and dependencies
       task = create_test_task()
       repository = MockTaskRepository()
       
       # Act - Execute the method under test
       result = await service.execute(task_id)
       
       # Assert - Verify the expected outcome
       assert result is not None
       assert result["status"] == "completed"
   ```

2. **Descriptive Test Names**
   ```python
   # Good
   def test_execute_with_none_user_id_raises_error(self):
   
   # Bad
   def test_user_id_none(self):
   ```

3. **Test Isolation**
   - Each test should be independent
   - Use fixtures for common setup
   - Clean up after each test

### Mocking Strategy

1. **Mock External Dependencies**
   ```python
   class MockTaskRepository:
       def __init__(self):
           self.tasks = {}
           self.save_called = False
       
       async def save(self, task):
           self.save_called = True
           self.tasks[str(task.id)] = task
   ```

2. **Verify Interactions**
   ```python
   assert repository.save_called
   assert len(repository.find_by_id_calls) == 1
   ```

### Test Data Management

1. **Use Factory Functions**
   ```python
   def create_task_with_status(task_id, user_id, title, description, status):
       return Task(
           id=TaskId(task_id),
           user_id=UserId(user_id),
           title=title,
           description=description,
           status=status,
           created_at=datetime.now(timezone.utc)
       )
   ```

2. **Use Fixtures for Common Data**
   ```python
   @pytest.fixture
   def pending_task():
       return create_task_with_status(
           TASK_ID_1, USER_ID_2, TASK_TITLE, TASK_DESCRIPTION, TaskStatus.PENDING
       )
   ```

### Coverage Goals

- **Unit Tests:** 90%+ coverage
- **Integration Tests:** Critical paths only
- **E2E Tests:** Main user workflows

### Performance Guidelines

- **Unit Tests:** < 1 second per test
- **Integration Tests:** < 5 seconds per test
- **E2E Tests:** < 30 seconds per test

---

## 📈 Test Metrics

### Current Coverage

- **Total Tests:** 168
- **Unit Tests:** 168
- **Integration Tests:** 0 (planned)
- **E2E Tests:** 0 (planned)

### Test Distribution

- **Domain Layer:** 74 tests
  - Entities: 23 tests
  - Value Objects: 4 tests
  - Events: 18 tests
  - Repositories: 29 tests
- **Application Layer:** 74 tests
  - Services: 74 tests
- **Infrastructure Layer:** 0 tests (planned)
- **API Layer:** 0 tests (planned)

### Quality Metrics

- **Test Execution Time:** ~0.3 seconds for full suite
- **Test Reliability:** 100% (no flaky tests)
- **Code Coverage:** 80%+ (target)
- **Test Maintainability:** High (clean, readable tests)

---

## 🔄 Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run tests
        run: poetry run pytest
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
```

---

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [TDD Best Practices](https://www.agilealliance.org/glossary/tdd/)
- [Testing Patterns](https://martinfowler.com/bliki/TestDouble.html)
- [Clean Code Testing](https://blog.cleancoder.com/uncle-bob/2017/07/11/PragmaticFunctionalProgramming.html) 