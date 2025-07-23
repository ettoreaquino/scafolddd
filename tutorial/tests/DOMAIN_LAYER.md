# Domain Layer Testing Guide

> **Complete testing implementation for the Domain Layer following TDD principles.**

This guide shows you exactly what tests to write when implementing the Domain Layer from scratch, following Test-Driven Development (TDD) approach.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Value Objects Tests](#value-objects-tests)
- [Entity Tests](#entity-tests)
- [Domain Events Tests](#domain-events-tests)
- [Repository Interface Tests](#repository-interface-tests)
- [Running Domain Tests](#running-domain-tests)
- [TDD Workflow](#tdd-workflow)

---

## 🎯 Overview

The Domain Layer contains the core business logic and rules. We test it thoroughly to ensure:

- ✅ **Business rules are enforced** - Validation and constraints work correctly
- ✅ **Domain events are generated** - State changes trigger appropriate events
- ✅ **Value objects are immutable** - Data integrity is maintained
- ✅ **Repository contracts are defined** - Clear interfaces for data access

## 🏗️ Test Structure

```
tests/unit/domain/
├── test_value_objects.py    # Value object tests (4 tests)
├── test_entities.py         # Entity tests (23 tests)
├── test_events.py           # Domain event tests (18 tests)
└── test_repositories.py     # Repository interface tests (29 tests)
```

**Total Domain Tests:** 74 tests

---

## 🔢 Value Objects Tests

### File: `tests/unit/domain/test_value_objects.py`

Value objects are immutable and represent domain concepts. Test their creation, validation, and behavior.

#### Test Categories:

1. **TaskId Tests**
   - Creation and validation
   - Generation of unique IDs
   - String representation
   - Equality and comparison

2. **UserId Tests**
   - Creation and validation
   - String representation
   - Equality and comparison

3. **TaskStatus Tests**
   - Enum values and validation
   - String representation
   - Status transitions

#### Example Test Implementation:

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
        assert isinstance(id1, TaskId)
        assert isinstance(id2, TaskId)
    
    def test_task_id_equality(self):
        """Test TaskId equality comparison"""
        id1 = TaskId("task-123")
        id2 = TaskId("task-123")
        id3 = TaskId("task-456")
        
        assert id1 == id2
        assert id1 != id3
        assert hash(id1) == hash(id2)
```

#### TDD Workflow for Value Objects:

1. **Write failing test** for TaskId creation
2. **Implement minimal TaskId class** to make test pass
3. **Write test** for TaskId generation
4. **Implement generate() method** to make test pass
5. **Write test** for equality comparison
6. **Implement __eq__ and __hash__** methods
7. **Refactor** while keeping tests green

---

## 🏛️ Entity Tests

### File: `tests/unit/domain/test_entities.py`

Entities represent business objects with identity and lifecycle. Test their behavior, state changes, and business rules.

#### Test Categories:

1. **Task Creation Tests**
   - Valid task creation
   - Business rule validation
   - Domain event generation

2. **Task State Management Tests**
   - Status transitions
   - Business rule enforcement
   - Event generation on state changes

3. **Task Validation Tests**
   - Title validation (empty, too long)
   - Description validation
   - Required field validation

4. **Task Event Generation Tests**
   - TaskCreated event on creation
   - TaskStatusChanged event on status update
   - TaskCompleted event on completion

#### Example Test Implementation:

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
        assert events[0].task_title == "Test Task"
        assert events[0].user_id == "user-456"
    
    def test_task_completion_generates_events(self):
        """Test that completing a task generates appropriate events"""
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Clear creation event
        task.pop_events()
        
        # Complete the task
        task.update_status(TaskStatus.COMPLETED)
        
        events = task.pop_events()
        assert len(events) == 2  # StatusChanged + TaskCompleted
        
        # Find the TaskCompleted event
        completed_events = [e for e in events if isinstance(e, TaskCompleted)]
        assert len(completed_events) == 1
        assert completed_events[0].task_title == "Test Task"
    
    def test_task_validation_empty_title(self):
        """Test that empty title raises validation error"""
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id=TaskId("task-123"),
                user_id=UserId("user-456"),
                title="",
                description="Test",
                status=TaskStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
```

#### TDD Workflow for Entities:

1. **Write test** for task creation with event generation
2. **Implement Task class** with basic structure and event generation
3. **Write test** for status updates and event generation
4. **Implement update_status method** with event generation
5. **Write test** for validation rules
6. **Implement validation logic** in __init__ method
7. **Write test** for business rules (e.g., completion logic)
8. **Implement business logic** methods
9. **Refactor** while keeping tests green

---

## 📢 Domain Events Tests

### File: `tests/unit/domain/test_events.py`

Domain events represent something that happened in the domain. Test their creation, serialization, and metadata.

#### Test Categories:

1. **TaskCreated Event Tests**
   - Event creation and validation
   - Event metadata (timestamp, aggregate_id)
   - Event serialization

2. **TaskStatusChanged Event Tests**
   - Event creation with old and new status
   - Status transition validation
   - Event metadata

3. **TaskCompleted Event Tests**
   - Event creation on task completion
   - Completion timestamp validation
   - Event metadata

4. **Base DomainEvent Tests**
   - Common event properties
   - Event inheritance
   - Event comparison

#### Example Test Implementation:

```python
@pytest.mark.domain
@pytest.mark.unit
class TestTaskCreated:
    def test_task_created_event_creation(self):
        """Test TaskCreated event creation"""
        timestamp = datetime.now(timezone.utc)
        event = TaskCreated(
            event_id="evt-123",
            timestamp=timestamp,
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        assert event.aggregate_id == "task-456"
        assert event.task_title == "Test Task"
        assert event.user_id == "user-789"
        assert event.timestamp == timestamp
        assert event.event_id == "evt-123"
    
    def test_task_created_event_serialization(self):
        """Test TaskCreated event serialization"""
        event = TaskCreated(
            event_id="evt-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        data = event.to_dict()
        assert data["event_type"] == "TaskCreated"
        assert data["task_title"] == "Test Task"
        assert data["user_id"] == "user-789"
```

#### TDD Workflow for Domain Events:

1. **Write test** for TaskCreated event creation
2. **Implement TaskCreated class** with required properties
3. **Write test** for event serialization
4. **Implement to_dict method** for serialization
5. **Write test** for event metadata validation
6. **Implement validation logic** in event constructors
7. **Write test** for event inheritance
8. **Implement base DomainEvent class**
9. **Refactor** while keeping tests green

---

## 🗄️ Repository Interface Tests

### File: `tests/unit/domain/test_repositories.py`

Repository interfaces define contracts for data access. Test the interface contracts using mocks.

#### Test Categories:

1. **TaskRepository Interface Tests**
   - Method contracts and signatures
   - Return type validation
   - Error handling expectations

2. **Mock Repository Tests**
   - Mock behavior verification
   - Method call tracking
   - Data persistence simulation

3. **Repository Method Tests**
   - save() method contract
   - find_by_id() method contract
   - find_by_user_id() method contract
   - delete() method contract

#### Example Test Implementation:

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
        assert mock_repository.saved_task == task
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_task(self, mock_repository):
        """Test finding a task by ID"""
        task = create_test_task()
        mock_repository.tasks[str(task.id)] = task
        
        found_task = await mock_repository.find_by_id(task.id)
        
        assert found_task == task
        assert mock_repository.find_by_id_called
        assert mock_repository.find_by_id_calls[0] == task.id
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_not_found(self, mock_repository):
        """Test finding a task that doesn't exist"""
        task_id = TaskId("non-existent")
        
        found_task = await mock_repository.find_by_id(task_id)
        
        assert found_task is None
        assert mock_repository.find_by_id_called
```

#### TDD Workflow for Repository Interfaces:

1. **Write test** for repository save method
2. **Define TaskRepository interface** with save method
3. **Write test** for find_by_id method
4. **Add find_by_id method** to interface
5. **Write test** for find_by_user_id method
6. **Add find_by_user_id method** to interface
7. **Write test** for delete method
8. **Add delete method** to interface
9. **Refactor** while keeping tests green

---

## 🚀 Running Domain Tests

### Basic Commands

```bash
# Run all domain layer tests
make test-domain

# Run specific domain test file
poetry run pytest tests/unit/domain/test_entities.py

# Run specific test class
poetry run pytest tests/unit/domain/test_entities.py::TestTask

# Run specific test method
poetry run pytest tests/unit/domain/test_entities.py::TestTask::test_task_creation_generates_event

# Run with coverage
poetry run pytest tests/unit/domain/ --cov=src.domain --cov-report=html
```

### Test Execution

```bash
# Expected output for domain tests
poetry run pytest tests/unit/domain/ -v

# Output:
# tests/unit/domain/test_value_objects.py::TestTaskId::test_task_id_creation PASSED
# tests/unit/domain/test_value_objects.py::TestTaskId::test_task_id_generation PASSED
# tests/unit/domain/test_entities.py::TestTask::test_task_creation_generates_event PASSED
# ...
# 74 passed in 0.15s
```

---

## 🔄 TDD Workflow

### Step-by-Step Implementation

1. **Start with Value Objects**
   ```bash
   # Write test first
   poetry run pytest tests/unit/domain/test_value_objects.py::TestTaskId::test_task_id_creation -v
   # Test fails (expected)
   
   # Implement minimal code
   # Edit src/domain/value_objects.py
   
   # Run test again
   poetry run pytest tests/unit/domain/test_value_objects.py::TestTaskId::test_task_id_creation -v
   # Test passes
   ```

2. **Continue with Entities**
   ```bash
   # Write entity test
   poetry run pytest tests/unit/domain/test_entities.py::TestTask::test_task_creation_generates_event -v
   # Test fails
   
   # Implement entity
   # Edit src/domain/entities.py
   
   # Run test again
   poetry run pytest tests/unit/domain/test_entities.py::TestTask::test_task_creation_generates_event -v
   # Test passes
   ```

3. **Add Domain Events**
   ```bash
   # Write event test
   poetry run pytest tests/unit/domain/test_events.py::TestTaskCreated::test_task_created_event_creation -v
   # Test fails
   
   # Implement event
   # Edit src/domain/events.py
   
   # Run test again
   poetry run pytest tests/unit/domain/test_events.py::TestTaskCreated::test_task_created_event_creation -v
   # Test passes
   ```

4. **Define Repository Interfaces**
   ```bash
   # Write repository test
   poetry run pytest tests/unit/domain/test_repositories.py::TestTaskRepository::test_save_task -v
   # Test fails
   
   # Implement interface
   # Edit src/domain/repositories.py
   
   # Run test again
   poetry run pytest tests/unit/domain/test_repositories.py::TestTaskRepository::test_save_task -v
   # Test passes
   ```

### Verification

After implementing all domain layer components:

```bash
# Run all domain tests
make test-domain

# Expected output:
# ============================= test session starts ==============================
# collected 74 items
# tests/unit/domain/test_entities.py ........................ [ 31%]
# tests/unit/domain/test_events.py .......................... [ 56%]
# tests/unit/domain/test_repositories.py ................... [ 95%]
# tests/unit/domain/test_value_objects.py .... [100%]
# ============================= 74 passed in 0.15s ==============================
```

---

## 📊 Test Coverage Goals

- **Value Objects:** 100% coverage
- **Entities:** 95%+ coverage
- **Domain Events:** 100% coverage
- **Repository Interfaces:** 100% coverage

### Coverage Report

```bash
poetry run pytest tests/unit/domain/ --cov=src.domain --cov-report=term-missing

# Expected coverage:
# Name                           Stmts   Miss  Cover   Missing
# ------------------------------------------------------------
# src/domain/entities.py            45      0   100%
# src/domain/events.py              35      0   100%
# src/domain/repositories.py        15      0   100%
# src/domain/value_objects.py       25      0   100%
# ------------------------------------------------------------
# TOTAL                            120      0   100%
```

---

## 🔗 Related Files

- **Implementation:** [TUTORIAL.md](../docs/TUTORIAL.md#domain-layer-implementation)
- **Testing Strategy:** [TESTS.md](../docs/TESTS.md)
- **Next Layer:** [APPLICATION_LAYER.md](APPLICATION_LAYER.md)

---

## ✅ Checklist

Before moving to the Application Layer, ensure:

- [ ] All 74 domain tests pass
- [ ] Value objects are immutable and validated
- [ ] Entities generate appropriate domain events
- [ ] Business rules are enforced
- [ ] Repository interfaces are defined
- [ ] Test coverage is 95%+
- [ ] All tests follow TDD principles

**Next Step:** [Application Layer Implementation](../docs/TUTORIAL.md#application-layer-implementation) 