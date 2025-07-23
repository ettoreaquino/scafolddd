# Application Layer Testing Guide

> **Complete testing implementation for the Application Layer following TDD principles.**

This guide shows you exactly what tests to write when implementing the Application Layer from scratch, following Test-Driven Development (TDD) approach.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Service Tests](#service-tests)
- [Mock Dependencies](#mock-dependencies)
- [Running Application Tests](#running-application-tests)
- [TDD Workflow](#tdd-workflow)

---

## 🎯 Overview

The Application Layer orchestrates domain objects and coordinates with infrastructure. We test it thoroughly to ensure:

- ✅ **Business use cases are implemented** - Services handle user workflows correctly
- ✅ **Dependencies are properly injected** - Services work with any implementation
- ✅ **Input validation works** - Invalid inputs are handled gracefully
- ✅ **Domain events are published** - Events are sent to the event bus
- ✅ **Error handling is robust** - Failures are handled appropriately

## 🏗️ Test Structure

```
tests/unit/application/
└── test_services.py         # Service tests (74 tests)
    ├── TestCreateTaskService (18 tests)
    ├── TestGetTaskService (18 tests)
    ├── TestCompleteTaskService (18 tests)
    └── TestListTasksService (18 tests)
```

**Total Application Tests:** 74 tests

---

## 🎯 Service Tests

### File: `tests/unit/application/test_services.py`

Application services implement business use cases. Test their behavior, dependency injection, and error handling.

#### Test Categories for Each Service:

1. **Initialization Tests**
   - Service dependency injection
   - Constructor validation

2. **Input Validation Tests**
   - Parameter validation
   - Error handling for invalid inputs

3. **Successful Execution Tests**
   - Happy path scenarios
   - Correct return values

4. **Repository Interaction Tests**
   - Service-repository communication
   - Method call verification

5. **Event Publishing Tests**
   - Domain event publishing
   - Event bus interaction

6. **Edge Cases Tests**
   - Boundary conditions
   - Error scenarios

#### Example Test Implementation:

```python
@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskService:
    def test_service_initialization_with_dependencies(self, task_repository, event_bus):
        """Test that service initializes with dependencies"""
        service = CreateTaskService(task_repository, event_bus)
        assert service.task_repository == task_repository
        assert service.event_bus == event_bus
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_inputs_creates_task(self, create_task_service, task_repository, event_bus):
        """Test that service creates task with valid inputs"""
        result = await create_task_service.execute("user-123", "Test Task", "Test Description")
        
        assert result is not None
        assert "task_id" in result
        assert result["title"] == "Test Task"
        assert result["description"] == "Test Description"
        assert result["user_id"] == "user-123"
        assert result["status"] == "pending"
        assert "created_at" in result
    
    @pytest.mark.asyncio
    async def test_execute_saves_task_to_repository(self, create_task_service, task_repository, event_bus):
        """Test that service saves task to repository"""
        await create_task_service.execute("user-123", "Test Task", "Test Description")
        
        assert task_repository.save_called
        assert len(task_repository.tasks) == 1
        
        saved_task = list(task_repository.tasks.values())[0]
        assert saved_task.title == "Test Task"
        assert saved_task.user_id.value == "user-123"
    
    @pytest.mark.asyncio
    async def test_execute_publishes_domain_events(self, create_task_service, task_repository, event_bus):
        """Test that service publishes domain events"""
        await create_task_service.execute("user-123", "Test Task", "Test Description")
        
        assert event_bus.publish_called
        assert len(event_bus.published_events) > 0
        
        # Check for TaskCreated event
        task_created_events = [e for e in event_bus.published_events if isinstance(e, TaskCreated)]
        assert len(task_created_events) == 1
        assert task_created_events[0].task_title == "Test Task"
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_title_raises_error(self, create_task_service):
        """Test that empty title raises validation error"""
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            await create_task_service.execute("user-123", "", "Test Description")
    
    @pytest.mark.asyncio
    async def test_execute_with_none_user_id_raises_error(self, create_task_service):
        """Test that None user_id raises validation error"""
        with pytest.raises(ValueError, match="User ID cannot be None or empty"):
            await create_task_service.execute(None, "Test Task", "Test Description")
```

#### TDD Workflow for Services:

1. **Write test** for service initialization
2. **Implement service constructor** with dependency injection
3. **Write test** for successful execution
4. **Implement execute method** with basic logic
5. **Write test** for repository interaction
6. **Add repository save call** to execute method
7. **Write test** for event publishing
8. **Add event publishing** to execute method
9. **Write test** for input validation
10. **Add validation logic** to execute method
11. **Refactor** while keeping tests green

---

## 🎭 Mock Dependencies

### Mock Repository

```python
class MockTaskRepository:
    """Mock implementation of TaskRepository for testing"""
    
    def __init__(self):
        self.tasks = {}
        self.save_called = False
        self.find_by_id_called = False
        self.find_by_id_calls = []
        self.find_by_user_id_called = False
        self.find_by_user_id_calls = []
        self.delete_called = False
        self.delete_calls = []
    
    async def save(self, task):
        """Mock save method"""
        self.save_called = True
        self.tasks[str(task.id)] = task
    
    async def find_by_id(self, task_id):
        """Mock find_by_id method"""
        self.find_by_id_called = True
        self.find_by_id_calls.append(task_id)
        return self.tasks.get(str(task_id))
    
    async def find_by_user_id(self, user_id):
        """Mock find_by_user_id method"""
        self.find_by_user_id_called = True
        self.find_by_user_id_calls.append(user_id)
        return [task for task in self.tasks.values() if str(task.user_id) == str(user_id)]
    
    async def delete(self, task_id):
        """Mock delete method"""
        self.delete_called = True
        self.delete_calls.append(task_id)
        if str(task_id) in self.tasks:
            del self.tasks[str(task_id)]
```

### Mock Event Bus

```python
class MockEventBus:
    """Mock implementation of EventBus for testing"""
    
    def __init__(self):
        self.published_events = []
        self.publish_called = False
    
    async def publish(self, events):
        """Mock publish method"""
        self.publish_called = True
        self.published_events.extend(events)
```

### Test Fixtures

```python
@pytest.fixture
def task_repository():
    """Create a mock task repository"""
    return MockTaskRepository()

@pytest.fixture
def event_bus():
    """Create a mock event bus"""
    return MockEventBus()

@pytest.fixture
def create_task_service(task_repository, event_bus):
    """Create a CreateTaskService instance with mocked dependencies"""
    return CreateTaskService(task_repository, event_bus)

@pytest.fixture
def get_task_service(task_repository):
    """Create a GetTaskService instance with mocked dependencies"""
    return GetTaskService(task_repository)

@pytest.fixture
def complete_task_service(task_repository, event_bus):
    """Create a CompleteTaskService instance with mocked dependencies"""
    return CompleteTaskService(task_repository, event_bus)

@pytest.fixture
def list_tasks_service(task_repository):
    """Create a ListTasksService instance with mocked dependencies"""
    return ListTasksService(task_repository)
```

---

## 🚀 Running Application Tests

### Basic Commands

```bash
# Run all application layer tests
poetry run pytest tests/unit/application/ -m application

# Run specific service tests
poetry run pytest tests/unit/application/test_services.py::TestCreateTaskService

# Run specific test method
poetry run pytest tests/unit/application/test_services.py::TestCreateTaskService::test_execute_with_valid_inputs_creates_task

# Run with coverage
poetry run pytest tests/unit/application/ --cov=src.application --cov-report=html
```

### Test Execution

```bash
# Expected output for application tests
poetry run pytest tests/unit/application/ -v

# Output:
# tests/unit/application/test_services.py::TestCreateTaskService::test_service_initialization_with_dependencies PASSED
# tests/unit/application/test_services.py::TestCreateTaskService::test_execute_with_valid_inputs_creates_task PASSED
# tests/unit/application/test_services.py::TestGetTaskService::test_service_initialization_with_dependencies PASSED
# ...
# 74 passed in 0.20s
```

---

## 🔄 TDD Workflow

### Step-by-Step Implementation

1. **Start with CreateTaskService**
   ```bash
   # Write test first
   poetry run pytest tests/unit/application/test_services.py::TestCreateTaskService::test_service_initialization_with_dependencies -v
   # Test fails (expected)
   
   # Implement minimal service
   # Edit src/application/services/create_task.py
   
   # Run test again
   poetry run pytest tests/unit/application/test_services.py::TestCreateTaskService::test_service_initialization_with_dependencies -v
   # Test passes
   ```

2. **Continue with GetTaskService**
   ```bash
   # Write test first
   poetry run pytest tests/unit/application/test_services.py::TestGetTaskService::test_service_initialization_with_dependencies -v
   # Test fails
   
   # Implement service
   # Edit src/application/services/get_task.py
   
   # Run test again
   poetry run pytest tests/unit/application/test_services.py::TestGetTaskService::test_service_initialization_with_dependencies -v
   # Test passes
   ```

3. **Add CompleteTaskService**
   ```bash
   # Write test first
   poetry run pytest tests/unit/application/test_services.py::TestCompleteTaskService::test_service_initialization_with_dependencies -v
   # Test fails
   
   # Implement service
   # Edit src/application/services/complete_task.py
   
   # Run test again
   poetry run pytest tests/unit/application/test_services.py::TestCompleteTaskService::test_service_initialization_with_dependencies -v
   # Test passes
   ```

4. **Add ListTasksService**
   ```bash
   # Write test first
   poetry run pytest tests/unit/application/test_services.py::TestListTasksService::test_service_initialization_with_dependencies -v
   # Test fails
   
   # Implement service
   # Edit src/application/services/list_tasks.py
   
   # Run test again
   poetry run pytest tests/unit/application/test_services.py::TestListTasksService::test_service_initialization_with_dependencies -v
   # Test passes
   ```

### Verification

After implementing all application services:

```bash
# Run all application tests
poetry run pytest tests/unit/application/ -v

# Expected output:
# ============================= test session starts ==============================
# collected 74 items
# tests/unit/application/test_services.py ................................ [100%]
# ============================= 74 passed in 0.20s ==============================
```

---

## 📊 Test Coverage Goals

- **CreateTaskService:** 95%+ coverage
- **GetTaskService:** 95%+ coverage
- **CompleteTaskService:** 95%+ coverage
- **ListTasksService:** 95%+ coverage

### Coverage Report

```bash
poetry run pytest tests/unit/application/ --cov=src.application --cov-report=term-missing

# Expected coverage:
# Name                                    Stmts   Miss  Cover   Missing
# ---------------------------------------------------------------------
# src/application/services/create_task.py    45      0   100%
# src/application/services/get_task.py       35      0   100%
# src/application/services/complete_task.py  40      0   100%
# src/application/services/list_tasks.py     30      0   100%
# ---------------------------------------------------------------------
# TOTAL                                    150      0   100%
```

---

## 🎯 Service-Specific Test Patterns

### CreateTaskService Tests

```python
@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskService:
    # Initialization tests
    def test_service_initialization_with_dependencies(self, task_repository, event_bus)
    
    # Input validation tests
    async def test_execute_with_empty_title_raises_error(self, create_task_service)
    async def test_execute_with_none_user_id_raises_error(self, create_task_service)
    async def test_execute_with_empty_user_id_raises_error(self, create_task_service)
    
    # Successful execution tests
    async def test_execute_with_valid_inputs_creates_task(self, create_task_service, task_repository, event_bus)
    async def test_execute_returns_correct_task_data(self, create_task_service, task_repository, event_bus)
    
    # Repository interaction tests
    async def test_execute_saves_task_to_repository(self, create_task_service, task_repository, event_bus)
    async def test_execute_calls_repository_save_once(self, create_task_service, task_repository, event_bus)
    
    # Event publishing tests
    async def test_execute_publishes_domain_events(self, create_task_service, task_repository, event_bus)
    async def test_execute_publishes_task_created_event(self, create_task_service, task_repository, event_bus)
    
    # Edge cases tests
    async def test_execute_with_long_title_raises_error(self, create_task_service)
    async def test_execute_with_none_description_uses_empty_string(self, create_task_service, task_repository, event_bus)
```

### GetTaskService Tests

```python
@pytest.mark.application
@pytest.mark.unit
class TestGetTaskService:
    # Initialization tests
    def test_service_initialization_with_dependencies(self, task_repository)
    
    # Input validation tests
    async def test_execute_with_none_task_id_raises_error(self, get_task_service)
    async def test_execute_with_empty_task_id_raises_error(self, get_task_service)
    
    # Successful execution tests
    async def test_execute_with_existing_task_returns_task(self, get_task_service, task_repository, in_progress_task)
    async def test_execute_returns_correct_task_data(self, get_task_service, task_repository, in_progress_task)
    
    # Repository interaction tests
    async def test_execute_calls_repository_find_by_id(self, get_task_service, task_repository, in_progress_task)
    async def test_execute_calls_repository_with_correct_task_id(self, get_task_service, task_repository, in_progress_task)
    
    # Error handling tests
    async def test_execute_with_nonexistent_task_returns_none(self, get_task_service, task_repository)
    async def test_execute_with_nonexistent_task_does_not_raise_error(self, get_task_service, task_repository)
```

### CompleteTaskService Tests

```python
@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskService:
    # Initialization tests
    def test_service_initialization_with_dependencies(self, task_repository, event_bus)
    
    # Input validation tests
    async def test_execute_with_none_task_id_raises_error(self, complete_task_service)
    async def test_execute_with_empty_task_id_raises_error(self, complete_task_service)
    
    # Successful execution tests
    async def test_execute_with_existing_task_completes_task(self, complete_task_service, task_repository, event_bus, in_progress_task)
    async def test_execute_returns_updated_task_data(self, complete_task_service, task_repository, event_bus, in_progress_task)
    
    # Repository interaction tests
    async def test_execute_calls_repository_find_by_id(self, complete_task_service, task_repository, event_bus, in_progress_task)
    async def test_execute_calls_repository_save(self, complete_task_service, task_repository, event_bus, in_progress_task)
    
    # Event publishing tests
    async def test_execute_publishes_domain_events(self, complete_task_service, task_repository, event_bus, in_progress_task)
    async def test_execute_publishes_task_completed_event(self, complete_task_service, task_repository, event_bus, in_progress_task)
    
    # Error handling tests
    async def test_execute_with_nonexistent_task_raises_error(self, complete_task_service, task_repository, event_bus)
    async def test_execute_with_already_completed_task_raises_error(self, complete_task_service, task_repository, event_bus, completed_task)
```

### ListTasksService Tests

```python
@pytest.mark.application
@pytest.mark.unit
class TestListTasksService:
    # Initialization tests
    def test_service_initialization_with_dependencies(self, task_repository)
    
    # Input validation tests
    async def test_execute_with_none_user_id_raises_error(self, list_tasks_service)
    async def test_execute_with_empty_user_id_raises_error(self, list_tasks_service)
    async def test_execute_with_whitespace_user_id_raises_error(self, list_tasks_service)
    
    # Successful execution tests
    async def test_execute_with_user_with_tasks_returns_task_list(self, list_tasks_service, task_repository, pending_task, in_progress_task)
    async def test_execute_with_user_with_no_tasks_returns_empty_list(self, list_tasks_service, task_repository)
    async def test_execute_returns_correct_task_data_structure(self, list_tasks_service, task_repository, pending_task)
    
    # Repository interaction tests
    async def test_execute_calls_repository_find_by_user_id(self, list_tasks_service, task_repository, pending_task)
    async def test_execute_calls_repository_with_correct_user_id(self, list_tasks_service, task_repository, pending_task)
    
    # Return value tests
    async def test_execute_returns_list_of_task_data(self, list_tasks_service, task_repository, pending_task, in_progress_task, completed_task)
    async def test_execute_preserves_all_task_properties(self, list_tasks_service, task_repository, in_progress_task)
    
    # Edge cases tests
    async def test_execute_with_user_with_mixed_task_statuses(self, list_tasks_service, task_repository, pending_task, in_progress_task, completed_task)
    async def test_execute_returns_tasks_sorted_by_creation_date(self, list_tasks_service, task_repository, old_task, new_task)
```

---

## 🔗 Related Files

- **Implementation:** [TUTORIAL.md](../docs/TUTORIAL.md#application-layer-implementation)
- **Testing Strategy:** [TESTS.md](../docs/TESTS.md)
- **Previous Layer:** [DOMAIN_LAYER.md](DOMAIN_LAYER.md)
- **Next Layer:** [INFRASTRUCTURE_LAYER.md](INFRASTRUCTURE_LAYER.md) (planned)

---

## ✅ Checklist

Before moving to the Infrastructure Layer, ensure:

- [ ] All 74 application tests pass
- [ ] All 4 services are implemented and tested
- [ ] Dependency injection works correctly
- [ ] Input validation is comprehensive
- [ ] Domain events are published
- [ ] Error handling is robust
- [ ] Test coverage is 95%+
- [ ] All tests follow TDD principles

**Next Step:** [Infrastructure Layer Implementation](../docs/TUTORIAL.md#infrastructure-layer-implementation) 