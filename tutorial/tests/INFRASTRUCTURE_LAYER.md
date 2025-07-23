# Infrastructure Layer Testing Guide

> **Complete testing implementation for the Infrastructure Layer following TDD principles.**

This guide shows you exactly what tests to write when implementing the Infrastructure Layer from scratch, following Test-Driven Development (TDD) approach.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Repository Implementation Tests](#repository-implementation-tests)
- [Event Bus Implementation Tests](#event-bus-implementation-tests)
- [Dependency Injection Tests](#dependency-injection-tests)
- [Integration Tests](#integration-tests)
- [Running Infrastructure Tests](#running-infrastructure-tests)
- [TDD Workflow](#tdd-workflow)

---

## 🎯 Overview

The Infrastructure Layer implements concrete adapters for external services. We test it thoroughly to ensure:

- ✅ **Repository implementations work correctly** - Data persistence and retrieval
- ✅ **Event bus implementations are reliable** - Event publishing and delivery
- ✅ **Dependency injection is configured properly** - Services are wired correctly
- ✅ **External service integration works** - DynamoDB, SNS, SQS integration
- ✅ **Error handling is robust** - Failures are handled gracefully

## 🏗️ Test Structure

```
tests/
├── unit/infrastructure/           # Unit tests (fast, isolated)
│   ├── test_dynamodb_repository.py # DynamoDB repository tests
│   ├── test_sns_event_bus.py      # SNS event bus tests
│   └── test_container.py          # Dependency injection tests
├── integration/                   # Integration tests (external dependencies)
│   ├── test_dynamodb_integration.py # Real DynamoDB tests
│   └── test_sns_integration.py    # Real SNS tests
└── e2e/                          # End-to-end tests (full system)
    └── test_infrastructure_e2e.py # Complete infrastructure tests
```

**Total Infrastructure Tests:** 50+ tests (planned)

---

## 🗄️ Repository Implementation Tests

### File: `tests/unit/infrastructure/test_dynamodb_repository.py`

Test the DynamoDB implementation of the TaskRepository interface.

#### Test Categories:

1. **Repository Interface Compliance Tests**
   - Verify all interface methods are implemented
   - Test method signatures and return types
   - Ensure error handling matches interface expectations

2. **DynamoDB Mapping Tests**
   - Test entity to DynamoDB item mapping
   - Test DynamoDB item to entity mapping
   - Verify single-table design implementation

3. **Query and Access Pattern Tests**
   - Test primary key queries (find_by_id)
   - Test GSI queries (find_by_user_id)
   - Test delete operations

4. **Error Handling Tests**
   - Test DynamoDB service errors
   - Test network failures
   - Test invalid data handling

#### Example Test Implementation:

```python
@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBTaskRepository:
    def test_repository_implements_interface(self):
        """Test that repository implements TaskRepository interface"""
        repository = DynamoDBTaskRepository("test-table")
        assert hasattr(repository, 'save')
        assert hasattr(repository, 'find_by_id')
        assert hasattr(repository, 'find_by_user_id')
        assert hasattr(repository, 'delete')
    
    @pytest.mark.asyncio
    async def test_save_task_maps_to_dynamodb_item(self, mock_dynamodb_table):
        """Test that task is correctly mapped to DynamoDB item"""
        repository = DynamoDBTaskRepository("test-table")
        task = create_test_task()
        
        await repository.save(task)
        
        # Verify item was saved with correct structure
        item = mock_dynamodb_table.get_item(
            Key={'PK': f'TASK#{task.id}', 'SK': f'TASK#{task.id}'}
        )['Item']
        
        assert item['PK'] == f'TASK#{task.id}'
        assert item['SK'] == f'TASK#{task.id}'
        assert item['GSI1PK'] == f'USER#{task.user_id}'
        assert item['Type'] == 'Task'
        assert item['TaskId'] == str(task.id)
        assert item['Title'] == task.title
        assert item['Status'] == task.status.value
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_task(self, mock_dynamodb_table):
        """Test finding a task by ID"""
        repository = DynamoDBTaskRepository("test-table")
        task = create_test_task()
        
        # Save task first
        await repository.save(task)
        
        # Find task
        found_task = await repository.find_by_id(task.id)
        
        assert found_task is not None
        assert found_task.id == task.id
        assert found_task.title == task.title
        assert found_task.user_id == task.user_id
        assert found_task.status == task.status
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_user_tasks(self, mock_dynamodb_table):
        """Test finding tasks by user ID"""
        repository = DynamoDBTaskRepository("test-table")
        user_id = UserId("user-123")
        
        # Create multiple tasks for the same user
        tasks = []
        for i in range(3):
            task = create_task_with_user(user_id, f"Task {i}")
            tasks.append(task)
            await repository.save(task)
        
        # Find tasks by user ID
        found_tasks = await repository.find_by_user_id(user_id)
        
        assert len(found_tasks) == 3
        assert all(t.user_id == user_id for t in found_tasks)
        assert {t.title for t in found_tasks} == {f"Task {i}" for i in range(3)}
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_not_found(self, mock_dynamodb_table):
        """Test finding a task that doesn't exist"""
        repository = DynamoDBTaskRepository("test-table")
        task_id = TaskId("non-existent")
        
        found_task = await repository.find_by_id(task_id)
        
        assert found_task is None
    
    @pytest.mark.asyncio
    async def test_delete_task_removes_from_dynamodb(self, mock_dynamodb_table):
        """Test deleting a task"""
        repository = DynamoDBTaskRepository("test-table")
        task = create_test_task()
        
        # Save task first
        await repository.save(task)
        
        # Verify task exists
        found_task = await repository.find_by_id(task.id)
        assert found_task is not None
        
        # Delete task
        await repository.delete(task.id)
        
        # Verify task is deleted
        found_task = await repository.find_by_id(task.id)
        assert found_task is None
```

#### TDD Workflow for Repository:

1. **Write test** for repository interface compliance
2. **Implement basic repository class** with interface methods
3. **Write test** for DynamoDB item mapping
4. **Implement entity to DynamoDB mapping** logic
5. **Write test** for save operation
6. **Implement save method** with DynamoDB put_item
7. **Write test** for find_by_id operation
8. **Implement find_by_id method** with DynamoDB get_item
9. **Write test** for find_by_user_id operation
10. **Implement find_by_user_id method** with GSI query
11. **Refactor** while keeping tests green

---

## 📢 Event Bus Implementation Tests

### File: `tests/unit/infrastructure/test_sns_event_bus.py`

Test the SNS implementation of the EventBus interface.

#### Test Categories:

1. **Event Bus Interface Compliance Tests**
   - Verify interface methods are implemented
   - Test method signatures and error handling

2. **Event Serialization Tests**
   - Test domain events to SNS message mapping
   - Test message format and structure
   - Verify event metadata is preserved

3. **SNS Publishing Tests**
   - Test successful event publishing
   - Test SNS service errors
   - Test network failures

4. **Event Ordering Tests**
   - Test events are published in correct order
   - Test batch publishing behavior

#### Example Test Implementation:

```python
@pytest.mark.infrastructure
@pytest.mark.unit
class TestSNSEventBus:
    def test_event_bus_implements_interface(self):
        """Test that SNS event bus implements EventBus interface"""
        mock_sns_client = Mock()
        event_bus = SNSEventBus(mock_sns_client, "arn:aws:sns:us-east-1:123456789012:test-topic")
        assert hasattr(event_bus, 'publish')
    
    @pytest.mark.asyncio
    async def test_publish_event_serializes_correctly(self, mock_sns_client):
        """Test that events are serialized correctly for SNS"""
        event_bus = SNSEventBus(mock_sns_client, "arn:aws:sns:us-east-1:123456789012:test-topic")
        
        event = TaskCreated(
            event_id="evt-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        await event_bus.publish([event])
        
        # Verify SNS publish was called
        assert mock_sns_client.publish.called
        
        # Verify message format
        call_args = mock_sns_client.publish.call_args
        assert call_args[1]['TopicArn'] == "arn:aws:sns:us-east-1:123456789012:test-topic"
        
        message = json.loads(call_args[1]['Message'])
        assert message['event_type'] == 'TaskCreated'
        assert message['event_data']['task_title'] == 'Test Task'
        assert message['event_data']['user_id'] == 'user-789'
    
    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, mock_sns_client):
        """Test publishing multiple events"""
        event_bus = SNSEventBus(mock_sns_client, "arn:aws:sns:us-east-1:123456789012:test-topic")
        
        events = [
            TaskCreated(event_id="evt-1", timestamp=datetime.now(timezone.utc), aggregate_id="task-1", task_title="Task 1", user_id="user-1"),
            TaskCompleted(event_id="evt-2", timestamp=datetime.now(timezone.utc), aggregate_id="task-1", task_title="Task 1", user_id="user-1", completed_at=datetime.now(timezone.utc))
        ]
        
        await event_bus.publish(events)
        
        # Verify SNS publish was called twice
        assert mock_sns_client.publish.call_count == 2
        
        # Verify both events were published
        calls = mock_sns_client.publish.call_args_list
        message1 = json.loads(calls[0][1]['Message'])
        message2 = json.loads(calls[1][1]['Message'])
        
        assert message1['event_type'] == 'TaskCreated'
        assert message2['event_type'] == 'TaskCompleted'
    
    @pytest.mark.asyncio
    async def test_publish_handles_sns_errors(self, mock_sns_client):
        """Test that SNS errors are handled gracefully"""
        mock_sns_client.publish.side_effect = Exception("SNS service error")
        event_bus = SNSEventBus(mock_sns_client, "arn:aws:sns:us-east-1:123456789012:test-topic")
        
        event = TaskCreated(
            event_id="evt-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        with pytest.raises(Exception, match="SNS service error"):
            await event_bus.publish([event])
```

#### TDD Workflow for Event Bus:

1. **Write test** for interface compliance
2. **Implement basic SNSEventBus class** with interface
3. **Write test** for event serialization
4. **Implement event to SNS message mapping**
5. **Write test** for successful publishing
6. **Implement publish method** with SNS client
7. **Write test** for multiple events
8. **Implement batch publishing logic**
9. **Write test** for error handling
10. **Implement error handling and retry logic**
11. **Refactor** while keeping tests green

---

## 🔧 Dependency Injection Tests

### File: `tests/unit/infrastructure/test_container.py`

Test the dependency injection container configuration.

#### Test Categories:

1. **Container Configuration Tests**
   - Test container initialization
   - Test configuration loading
   - Test environment-specific settings

2. **Service Registration Tests**
   - Test services are registered correctly
   - Test dependency resolution
   - Test singleton vs factory patterns

3. **Service Wiring Tests**
   - Test services are wired with correct dependencies
   - Test circular dependency detection
   - Test optional dependencies

#### Example Test Implementation:

```python
@pytest.mark.infrastructure
@pytest.mark.unit
class TestContainer:
    def test_container_initialization(self):
        """Test that container initializes correctly"""
        container = Container()
        assert container is not None
        assert hasattr(container, 'config')
        assert hasattr(container, 'task_repository')
        assert hasattr(container, 'event_bus')
        assert hasattr(container, 'create_task')
        assert hasattr(container, 'get_task')
        assert hasattr(container, 'complete_task')
        assert hasattr(container, 'list_tasks')
    
    def test_container_configuration(self):
        """Test that container loads configuration correctly"""
        container = Container()
        container.config.table_name.from_value("test-tasks")
        container.config.topic_arn.from_value("arn:aws:sns:us-east-1:123456789012:test-topic")
        
        assert container.config.table_name() == "test-tasks"
        assert container.config.topic_arn() == "arn:aws:sns:us-east-1:123456789012:test-topic"
    
    def test_task_repository_registration(self):
        """Test that task repository is registered correctly"""
        container = Container()
        container.config.table_name.from_value("test-tasks")
        
        repository = container.task_repository()
        assert isinstance(repository, DynamoDBTaskRepository)
        assert repository.table_name == "test-tasks"
    
    def test_event_bus_registration(self):
        """Test that event bus is registered correctly"""
        container = Container()
        container.config.topic_arn.from_value("arn:aws:sns:us-east-1:123456789012:test-topic")
        
        event_bus = container.event_bus()
        assert isinstance(event_bus, SNSEventBus)
        assert event_bus.topic_arn == "arn:aws:sns:us-east-1:123456789012:test-topic"
    
    def test_service_registration(self):
        """Test that application services are registered correctly"""
        container = Container()
        
        create_service = container.create_task()
        assert isinstance(create_service, CreateTaskService)
        assert create_service.task_repository is not None
        assert create_service.event_bus is not None
        
        get_service = container.get_task()
        assert isinstance(get_service, GetTaskService)
        assert get_service.task_repository is not None
        
        complete_service = container.complete_task()
        assert isinstance(complete_service, CompleteTaskService)
        assert complete_service.task_repository is not None
        assert complete_service.event_bus is not None
        
        list_service = container.list_tasks()
        assert isinstance(list_service, ListTasksService)
        assert list_service.task_repository is not None
```

#### TDD Workflow for Container:

1. **Write test** for container initialization
2. **Implement basic Container class** with configuration
3. **Write test** for configuration loading
4. **Implement configuration management**
5. **Write test** for service registration
6. **Implement service registration methods**
7. **Write test** for dependency wiring
8. **Implement dependency injection logic**
9. **Write test** for service instantiation
10. **Implement service factory methods**
11. **Refactor** while keeping tests green

---

## 🔗 Integration Tests

### File: `tests/integration/test_dynamodb_integration.py`

Test integration with real DynamoDB (using moto for mocking).

#### Test Categories:

1. **Real DynamoDB Integration Tests**
   - Test with actual DynamoDB table
   - Test table creation and schema
   - Test real query performance

2. **End-to-End Repository Tests**
   - Test complete CRUD operations
   - Test with real data persistence
   - Test concurrent access patterns

#### Example Test Implementation:

```python
@pytest.mark.integration
@pytest.mark.asyncio
class TestDynamoDBIntegration:
    async def test_real_dynamodb_operations(self, dynamodb_table):
        """Test real DynamoDB operations with moto"""
        repository = DynamoDBTaskRepository("test-tasks")
        
        # Create and save task
        task = create_test_task()
        await repository.save(task)
        
        # Verify task was saved
        found_task = await repository.find_by_id(task.id)
        assert found_task is not None
        assert found_task.id == task.id
        assert found_task.title == task.title
        
        # Test find by user ID
        user_tasks = await repository.find_by_user_id(task.user_id)
        assert len(user_tasks) == 1
        assert user_tasks[0].id == task.id
        
        # Test delete
        await repository.delete(task.id)
        deleted_task = await repository.find_by_id(task.id)
        assert deleted_task is None
    
    async def test_concurrent_access(self, dynamodb_table):
        """Test concurrent access to DynamoDB"""
        repository = DynamoDBTaskRepository("test-tasks")
        
        # Create multiple tasks concurrently
        tasks = [create_test_task() for _ in range(5)]
        
        # Save all tasks concurrently
        await asyncio.gather(*[repository.save(task) for task in tasks])
        
        # Verify all tasks were saved
        for task in tasks:
            found_task = await repository.find_by_id(task.id)
            assert found_task is not None
            assert found_task.id == task.id
```

### File: `tests/integration/test_sns_integration.py`

Test integration with real SNS (using moto for mocking).

#### Example Test Implementation:

```python
@pytest.mark.integration
@pytest.mark.asyncio
class TestSNSIntegration:
    async def test_real_sns_publishing(self, sns_topic):
        """Test real SNS publishing with moto"""
        event_bus = SNSEventBus(sns_topic.client, sns_topic.arn)
        
        event = TaskCreated(
            event_id="evt-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        # Publish event
        await event_bus.publish([event])
        
        # Verify event was published (check SNS topic messages)
        messages = sns_topic.get_messages()
        assert len(messages) == 1
        
        message = json.loads(messages[0]['Message'])
        assert message['event_type'] == 'TaskCreated'
        assert message['event_data']['task_title'] == 'Test Task'
```

---

## 🚀 Running Infrastructure Tests

### Basic Commands

```bash
# Run all infrastructure unit tests
poetry run pytest tests/unit/infrastructure/ -m infrastructure

# Run specific infrastructure test file
poetry run pytest tests/unit/infrastructure/test_dynamodb_repository.py

# Run integration tests
poetry run pytest tests/integration/ -m integration

# Run with coverage
poetry run pytest tests/unit/infrastructure/ --cov=src.infrastructure --cov-report=html
```

### Test Execution

```bash
# Expected output for infrastructure tests
poetry run pytest tests/unit/infrastructure/ -v

# Output:
# tests/unit/infrastructure/test_dynamodb_repository.py::TestDynamoDBTaskRepository::test_repository_implements_interface PASSED
# tests/unit/infrastructure/test_dynamodb_repository.py::TestDynamoDBTaskRepository::test_save_task_maps_to_dynamodb_item PASSED
# tests/unit/infrastructure/test_sns_event_bus.py::TestSNSEventBus::test_event_bus_implements_interface PASSED
# ...
# 50+ passed in 0.30s
```

---

## 🔄 TDD Workflow

### Step-by-Step Implementation

1. **Start with Repository Interface**
   ```bash
   # Write test first
   poetry run pytest tests/unit/infrastructure/test_dynamodb_repository.py::TestDynamoDBTaskRepository::test_repository_implements_interface -v
   # Test fails (expected)
   
   # Implement basic repository
   # Edit src/infrastructure/repositories/dynamodb_task_repository.py
   
   # Run test again
   poetry run pytest tests/unit/infrastructure/test_dynamodb_repository.py::TestDynamoDBTaskRepository::test_repository_implements_interface -v
   # Test passes
   ```

2. **Continue with Event Bus**
   ```bash
   # Write test first
   poetry run pytest tests/unit/infrastructure/test_sns_event_bus.py::TestSNSEventBus::test_event_bus_implements_interface -v
   # Test fails
   
   # Implement event bus
   # Edit src/infrastructure/event_bus/sns_event_bus.py
   
   # Run test again
   poetry run pytest tests/unit/infrastructure/test_sns_event_bus.py::TestSNSEventBus::test_event_bus_implements_interface -v
   # Test passes
   ```

3. **Add Dependency Injection**
   ```bash
   # Write test first
   poetry run pytest tests/unit/infrastructure/test_container.py::TestContainer::test_container_initialization -v
   # Test fails
   
   # Implement container
   # Edit src/infrastructure/container.py
   
   # Run test again
   poetry run pytest tests/unit/infrastructure/test_container.py::TestContainer::test_container_initialization -v
   # Test passes
   ```

### Verification

After implementing all infrastructure components:

```bash
# Run all infrastructure tests
poetry run pytest tests/unit/infrastructure/ -v

# Expected output:
# ============================= test session starts ==============================
# collected 50+ items
# tests/unit/infrastructure/test_container.py ................ [ 20%]
# tests/unit/infrastructure/test_dynamodb_repository.py ................ [ 60%]
# tests/unit/infrastructure/test_sns_event_bus.py ................ [100%]
# ============================= 50+ passed in 0.30s ==============================
```

---

## 📊 Test Coverage Goals

- **Repository Implementation:** 95%+ coverage
- **Event Bus Implementation:** 95%+ coverage
- **Dependency Injection:** 100% coverage
- **Integration Tests:** Critical paths only

### Coverage Report

```bash
poetry run pytest tests/unit/infrastructure/ --cov=src.infrastructure --cov-report=term-missing

# Expected coverage:
# Name                                    Stmts   Miss  Cover   Missing
# ---------------------------------------------------------------------
# src/infrastructure/container.py            45      0   100%
# src/infrastructure/repositories/           60      0   100%
# src/infrastructure/event_bus/              40      0   100%
# ---------------------------------------------------------------------
# TOTAL                                    145      0   100%
```

---

## 🔗 Related Files

- **Implementation:** [TUTORIAL.md](../TUTORIAL.md#infrastructure-layer-implementation)
- **Event Flow:** [EVENT_FLOW.md](../EVENT_FLOW.md)
- **Previous Layer:** [APPLICATION_LAYER.md](APPLICATION_LAYER.md)
- **Next Layer:** [API_LAYER.md](API_LAYER.md) (planned)

---

## ✅ Checklist

Before moving to the API Layer, ensure:

- [ ] All 50+ infrastructure tests pass
- [ ] DynamoDB repository is fully implemented and tested
- [ ] SNS event bus is fully implemented and tested
- [ ] Dependency injection container is configured
- [ ] Integration tests pass with real services
- [ ] Error handling is robust
- [ ] Test coverage is 95%+
- [ ] All tests follow TDD principles

**Next Step:** [API Layer Implementation](../TUTORIAL.md#api-adapter-layer-implementation) 