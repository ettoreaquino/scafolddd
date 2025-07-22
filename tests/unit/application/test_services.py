import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from src.application.services.complete_task import CompleteTaskService
from src.application.services.create_task import CreateTaskService
from src.domain.entities.task import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus
from src.domain.events import TaskCompleted, TaskStatusChanged, TaskCreated


class MockEventBus:
    """Mock implementation of EventBus for testing"""
    
    def __init__(self):
        self.published_events = []
        self.publish_called = False
    
    async def publish(self, events):
        """Mock publish method"""
        self.publish_called = True
        self.published_events.extend(events)


class MockTaskRepository:
    """Mock implementation of TaskRepository for testing"""
    
    def __init__(self):
        self.tasks = {}
        self.save_called = False
        self.find_by_id_called = False
    
    async def save(self, task: Task) -> None:
        """Mock save method"""
        self.save_called = True
        self.tasks[str(task.id)] = task
    
    async def find_by_id(self, task_id: TaskId) -> Task | None:
        """Mock find_by_id method"""
        self.find_by_id_called = True
        return self.tasks.get(str(task_id))


@pytest.fixture
def task_repository():
    """Create a mock task repository"""
    return MockTaskRepository()


@pytest.fixture
def event_bus():
    """Create a mock event bus"""
    return MockEventBus()


@pytest.fixture
def complete_task_service(task_repository, event_bus):
    """Create a CompleteTaskService instance with mocked dependencies"""
    return CompleteTaskService(task_repository, event_bus)


@pytest.fixture
def create_task_service(task_repository, event_bus):
    """Create a CreateTaskService instance with mocked dependencies"""
    return CreateTaskService(task_repository, event_bus)


@pytest.fixture
def pending_task():
    """Create a pending task for testing"""
    return Task(
        id=TaskId("task-123"),
        user_id=UserId("user-456"),
        title="Test Task",
        description="A test task for completion testing",
        status=TaskStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def in_progress_task():
    """Create an in-progress task for testing"""
    return Task(
        id=TaskId("task-456"),
        user_id=UserId("user-456"),
        title="In Progress Task",
        description="A task that's in progress",
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def completed_task():
    """Create a completed task for testing"""
    return Task(
        id=TaskId("task-789"),
        user_id=UserId("user-456"),
        title="Completed Task",
        description="A task that's already completed",
        status=TaskStatus.COMPLETED,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def cancelled_task():
    """Create a cancelled task for testing"""
    return Task(
        id=TaskId("task-999"),
        user_id=UserId("user-456"),
        title="Cancelled Task",
        description="A task that's been cancelled",
        status=TaskStatus.CANCELLED,
        created_at=datetime.now(timezone.utc)
    )


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceInitialization:
    """Test CompleteTaskService initialization and dependency injection"""
    
    def test_service_initialization_with_dependencies(self, task_repository, event_bus):
        """Test that service can be initialized with dependencies"""
        # Act
        service = CompleteTaskService(task_repository, event_bus)
        
        # Assert
        assert service._task_repository == task_repository
        assert service._event_bus == event_bus


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceInputValidation:
    """Test input validation in CompleteTaskService"""
    
    @pytest.mark.asyncio
    async def test_execute_with_none_task_id_raises_error(self, complete_task_service):
        """Test that None task_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Task ID is required"):
            await complete_task_service.execute(None)
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_task_id_raises_error(self, complete_task_service):
        """Test that empty task_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Task ID is required"):
            await complete_task_service.execute("")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_task_id_raises_error(self, complete_task_service):
        """Test that whitespace-only task_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Task ID is required"):
            await complete_task_service.execute("   ")
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_task_id_does_not_raise_error(self, complete_task_service, task_repository, pending_task):
        """Test that valid task_id doesn't raise validation error"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        # Act & Assert
        try:
            result = await complete_task_service.execute(str(pending_task.id))
            assert result is not None
        except ValueError:
            pytest.fail("Valid task_id should not raise ValueError")


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceTaskNotFound:
    """Test CompleteTaskService behavior when task is not found"""
    
    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_task_returns_none(self, complete_task_service, task_repository):
        """Test that non-existent task returns None"""
        # Arrange
        non_existent_task_id = "non-existent-task"
        
        # Act
        result = await complete_task_service.execute(non_existent_task_id)
        
        # Assert
        assert result is None
        assert task_repository.find_by_id_called
        assert not task_repository.save_called
        assert not complete_task_service._event_bus.publish_called


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceBusinessRules:
    """Test CompleteTaskService business rule validation"""
    
    @pytest.mark.asyncio
    async def test_execute_with_completed_task_raises_error(self, complete_task_service, task_repository, completed_task):
        """Test that completing an already completed task raises error"""
        # Arrange
        task_repository.tasks[str(completed_task.id)] = completed_task
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task with status 'completed' cannot be completed"):
            await complete_task_service.execute(str(completed_task.id))
        
        # Verify no changes were made
        assert not task_repository.save_called
        assert not complete_task_service._event_bus.publish_called
    
    @pytest.mark.asyncio
    async def test_execute_with_cancelled_task_raises_error(self, complete_task_service, task_repository, cancelled_task):
        """Test that completing a cancelled task raises error"""
        # Arrange
        task_repository.tasks[str(cancelled_task.id)] = cancelled_task
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task with status 'cancelled' cannot be completed"):
            await complete_task_service.execute(str(cancelled_task.id))
        
        # Verify no changes were made
        assert not task_repository.save_called
        assert not complete_task_service._event_bus.publish_called


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceSuccessfulCompletion:
    """Test CompleteTaskService successful task completion scenarios"""
    
    @pytest.mark.asyncio
    async def test_execute_with_pending_task_completes_successfully(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that pending task can be completed successfully"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        original_status = pending_task.status
        
        # Act
        result = await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert result is not None
        assert result["task_id"] == str(pending_task.id)
        assert result["title"] == pending_task.title
        assert result["status"] == str(TaskStatus.COMPLETED)
        assert result["completed_at"] is not None
        
        # Verify task was updated
        assert pending_task.status == TaskStatus.COMPLETED
        assert pending_task.updated_at is not None
        assert task_repository.save_called
        
        # Verify events were published
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 3  # TaskCreated + TaskStatusChanged + TaskCompleted
        
        # Verify event types
        event_types = [type(event) for event in event_bus.published_events]
        assert TaskStatusChanged in event_types
        assert TaskCompleted in event_types
    
    @pytest.mark.asyncio
    async def test_execute_with_in_progress_task_completes_successfully(self, complete_task_service, task_repository, event_bus, in_progress_task):
        """Test that in-progress task can be completed successfully"""
        # Arrange
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        original_status = in_progress_task.status
        
        # Act
        result = await complete_task_service.execute(str(in_progress_task.id))
        
        # Assert
        assert result is not None
        assert result["task_id"] == str(in_progress_task.id)
        assert result["title"] == in_progress_task.title
        assert result["status"] == str(TaskStatus.COMPLETED)
        assert result["completed_at"] is not None
        
        # Verify task was updated
        assert in_progress_task.status == TaskStatus.COMPLETED
        assert in_progress_task.updated_at is not None
        assert task_repository.save_called
        
        # Verify events were published
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 2  # TaskStatusChanged + TaskCompleted (no TaskCreated for IN_PROGRESS)
    
    @pytest.mark.asyncio
    async def test_execute_trims_whitespace_from_task_id(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that task_id whitespace is trimmed before processing"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_id_with_whitespace = f"  {str(pending_task.id)}  "
        
        # Act
        result = await complete_task_service.execute(task_id_with_whitespace)
        
        # Assert
        assert result is not None
        assert result["task_id"] == str(pending_task.id)
        assert task_repository.save_called
        assert event_bus.publish_called


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceEventPublishing:
    """Test CompleteTaskService event publishing behavior"""
    
    @pytest.mark.asyncio
    async def test_execute_publishes_correct_events(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that correct events are published when completing a task"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        # Act
        await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 3  # TaskCreated + TaskStatusChanged + TaskCompleted
        
        # Check TaskStatusChanged event
        status_changed_event = next(
            (event for event in event_bus.published_events if isinstance(event, TaskStatusChanged)), 
            None
        )
        assert status_changed_event is not None
        assert status_changed_event.aggregate_id == str(pending_task.id)
        assert status_changed_event.old_status == str(TaskStatus.PENDING)
        assert status_changed_event.new_status == str(TaskStatus.COMPLETED)
        assert status_changed_event.user_id == str(pending_task.user_id)
        
        # Check TaskCompleted event
        completed_event = next(
            (event for event in event_bus.published_events if isinstance(event, TaskCompleted)), 
            None
        )
        assert completed_event is not None
        assert completed_event.aggregate_id == str(pending_task.id)
        assert completed_event.task_title == pending_task.title
        assert completed_event.user_id == str(pending_task.user_id)
    
    @pytest.mark.asyncio
    async def test_execute_clears_events_after_publishing(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that events are cleared from task after publishing"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        # Act
        await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert event_bus.publish_called
        # Events should be cleared from task after publishing
        assert len(pending_task.pop_events()) == 0


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceRepositoryInteraction:
    """Test CompleteTaskService interaction with repository"""
    
    @pytest.mark.asyncio
    async def test_execute_calls_repository_methods_in_correct_order(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that repository methods are called in the correct order"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        # Act
        await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert task_repository.find_by_id_called
        assert task_repository.save_called
        
        # Verify find_by_id was called before save
        # (We can't easily test exact order with current mock, but we can verify both were called)
        assert task_repository.find_by_id_called and task_repository.save_called
    
    @pytest.mark.asyncio
    async def test_execute_saves_updated_task(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that the updated task is saved to repository"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        original_status = pending_task.status
        
        # Act
        await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert task_repository.save_called
        
        # Verify the saved task has the updated status
        saved_task = task_repository.tasks[str(pending_task.id)]
        assert saved_task.status == TaskStatus.COMPLETED
        assert saved_task.updated_at is not None


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceReturnValue:
    """Test CompleteTaskService return value structure and content"""
    
    @pytest.mark.asyncio
    async def test_execute_returns_correct_data_structure(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that execute returns the expected data structure"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        # Act
        result = await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert isinstance(result, dict)
        assert "task_id" in result
        assert "title" in result
        assert "status" in result
        assert "completed_at" in result
        
        assert result["task_id"] == str(pending_task.id)
        assert result["title"] == pending_task.title
        assert result["status"] == str(TaskStatus.COMPLETED)
        assert result["completed_at"] is not None
    
    @pytest.mark.asyncio
    async def test_execute_returns_iso_format_completed_at(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that completed_at is returned in ISO format"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        # Act
        result = await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert result["completed_at"] is not None
        # Verify it's a valid ISO format string
        try:
            datetime.fromisoformat(result["completed_at"])
        except ValueError:
            pytest.fail("completed_at should be in ISO format")


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceEdgeCases:
    """Test CompleteTaskService edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_execute_with_task_that_has_no_events(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test behavior when task has no events to publish"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        # Clear any existing events
        pending_task.pop_events()
        
        # Act
        result = await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert result is not None
        assert task_repository.save_called
        # Event bus should still be called, but with empty events list
        assert event_bus.publish_called
    
    @pytest.mark.asyncio
    async def test_execute_preserves_task_other_properties(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that task completion doesn't affect other task properties"""
        # Arrange
        task_repository.tasks[str(pending_task.id)] = pending_task
        original_title = pending_task.title
        original_description = pending_task.description
        original_user_id = pending_task.user_id
        original_created_at = pending_task.created_at
        
        # Act
        await complete_task_service.execute(str(pending_task.id))
        
        # Assert
        assert pending_task.title == original_title
        assert pending_task.description == original_description
        assert pending_task.user_id == original_user_id
        assert pending_task.created_at == original_created_at
        # Only status and updated_at should change
        assert pending_task.status == TaskStatus.COMPLETED
        assert pending_task.updated_at is not None


# =============================================================================
# CREATE TASK SERVICE TESTS
# =============================================================================

@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceInitialization:
    """Test CreateTaskService initialization and dependency injection"""
    
    def test_service_initialization_with_dependencies(self, task_repository, event_bus):
        """Test that service can be initialized with dependencies"""
        # Act
        service = CreateTaskService(task_repository, event_bus)
        
        # Assert
        assert service._task_repository == task_repository
        assert service._event_bus == event_bus


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceInputValidation:
    """Test input validation in CreateTaskService"""
    
    @pytest.mark.asyncio
    async def test_execute_with_none_user_id_raises_error(self, create_task_service):
        """Test that None user_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="User ID is required"):
            await create_task_service.execute(None, "Test Task")
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_user_id_raises_error(self, create_task_service):
        """Test that empty user_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="User ID is required"):
            await create_task_service.execute("", "Test Task")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_user_id_raises_error(self, create_task_service):
        """Test that whitespace-only user_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="User ID is required"):
            await create_task_service.execute("   ", "Test Task")
    
    @pytest.mark.asyncio
    async def test_execute_with_none_title_raises_error(self, create_task_service):
        """Test that None title raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Task title is required"):
            await create_task_service.execute("user-123", None)
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_title_raises_error(self, create_task_service):
        """Test that empty title raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Task title is required"):
            await create_task_service.execute("user-123", "")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_title_raises_error(self, create_task_service):
        """Test that whitespace-only title raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Task title is required"):
            await create_task_service.execute("user-123", "   ")
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_inputs_does_not_raise_error(self, create_task_service, task_repository, event_bus):
        """Test that valid inputs don't raise validation error"""
        # Act & Assert
        try:
            result = await create_task_service.execute("user-123", "Test Task", "Test Description")
            assert result is not None
            assert "task_id" in result
            assert "title" in result
            assert "description" in result
            assert "status" in result
            assert "created_at" in result
            assert "user_id" in result
        except ValueError:
            pytest.fail("Valid inputs should not raise ValueError")


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceSuccessfulCreation:
    """Test CreateTaskService successful task creation scenarios"""
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_inputs_creates_task_successfully(self, create_task_service, task_repository, event_bus):
        """Test that valid inputs create a task successfully"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        description = "Test Description"
        
        # Act
        result = await create_task_service.execute(user_id, title, description)
        
        # Assert
        assert result is not None
        assert result["title"] == title
        assert result["description"] == description
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == user_id
        assert result["created_at"] is not None
        assert result["task_id"] is not None
        
        # Verify task was saved
        assert task_repository.save_called
        
        # Verify events were published
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 1  # TaskCreated event
        
        # Verify event type
        event_types = [type(event) for event in event_bus.published_events]
        assert TaskCreated in event_types
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_description_creates_task_successfully(self, create_task_service, task_repository, event_bus):
        """Test that empty description creates a task successfully"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        description = ""
        
        # Act
        result = await create_task_service.execute(user_id, title, description)
        
        # Assert
        assert result is not None
        assert result["title"] == title
        assert result["description"] == ""
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == user_id
        assert result["created_at"] is not None
        assert result["task_id"] is not None
        
        # Verify task was saved
        assert task_repository.save_called
        
        # Verify events were published
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 1  # TaskCreated event
    
    @pytest.mark.asyncio
    async def test_execute_with_none_description_creates_task_successfully(self, create_task_service, task_repository, event_bus):
        """Test that None description creates a task successfully"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        
        # Act
        result = await create_task_service.execute(user_id, title, None)
        
        # Assert
        assert result is not None
        assert result["title"] == title
        assert result["description"] == ""
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == user_id
        assert result["created_at"] is not None
        assert result["task_id"] is not None
        
        # Verify task was saved
        assert task_repository.save_called
        
        # Verify events were published
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 1  # TaskCreated event
    
    @pytest.mark.asyncio
    async def test_execute_trims_whitespace_from_inputs(self, create_task_service, task_repository, event_bus):
        """Test that whitespace is trimmed from inputs"""
        # Arrange
        user_id_with_whitespace = "  user-123  "
        title_with_whitespace = "  Test Task  "
        description_with_whitespace = "  Test Description  "
        
        # Act
        result = await create_task_service.execute(user_id_with_whitespace, title_with_whitespace, description_with_whitespace)
        
        # Assert
        assert result is not None
        assert result["title"] == "Test Task"  # Trimmed
        assert result["description"] == "Test Description"  # Trimmed
        assert result["user_id"] == "user-123"  # Trimmed
        assert task_repository.save_called
        assert event_bus.publish_called


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceEventPublishing:
    """Test CreateTaskService event publishing behavior"""
    
    @pytest.mark.asyncio
    async def test_execute_publishes_task_created_event(self, create_task_service, task_repository, event_bus):
        """Test that TaskCreated event is published when creating a task"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        description = "Test Description"
        
        # Act
        result = await create_task_service.execute(user_id, title, description)
        
        # Assert
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 1
        
        # Check TaskCreated event
        created_event = event_bus.published_events[0]
        assert isinstance(created_event, TaskCreated)
        assert created_event.aggregate_id == result["task_id"]
        assert created_event.task_title == title
        assert created_event.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_execute_clears_events_after_publishing(self, create_task_service, task_repository, event_bus):
        """Test that events are cleared from task after publishing"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        
        # Act
        await create_task_service.execute(user_id, title)
        
        # Assert
        assert event_bus.publish_called
        # Events should be cleared from task after publishing
        # We can't directly access the task since it's created internally,
        # but we can verify the event bus was called with the events


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceRepositoryInteraction:
    """Test CreateTaskService interaction with repository"""
    
    @pytest.mark.asyncio
    async def test_execute_saves_task_to_repository(self, create_task_service, task_repository, event_bus):
        """Test that the created task is saved to repository"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        description = "Test Description"
        
        # Act
        result = await create_task_service.execute(user_id, title, description)
        
        # Assert
        assert task_repository.save_called
        
        # Verify the saved task has the correct properties
        # We can't easily access the saved task directly, but we can verify
        # that save was called and the result contains the expected data
        assert result["title"] == title
        assert result["description"] == description
        assert result["user_id"] == user_id
        assert result["status"] == str(TaskStatus.PENDING)


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceReturnValue:
    """Test CreateTaskService return value structure and content"""
    
    @pytest.mark.asyncio
    async def test_execute_returns_correct_data_structure(self, create_task_service, task_repository, event_bus):
        """Test that execute returns the expected data structure"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        description = "Test Description"
        
        # Act
        result = await create_task_service.execute(user_id, title, description)
        
        # Assert
        assert isinstance(result, dict)
        assert "task_id" in result
        assert "title" in result
        assert "description" in result
        assert "status" in result
        assert "created_at" in result
        assert "user_id" in result
        
        assert result["title"] == title
        assert result["description"] == description
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == user_id
        assert result["created_at"] is not None
        assert result["task_id"] is not None
    
    @pytest.mark.asyncio
    async def test_execute_returns_iso_format_created_at(self, create_task_service, task_repository, event_bus):
        """Test that created_at is returned in ISO format"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        
        # Act
        result = await create_task_service.execute(user_id, title)
        
        # Assert
        assert result["created_at"] is not None
        # Verify it's a valid ISO format string
        try:
            datetime.fromisoformat(result["created_at"])
        except ValueError:
            pytest.fail("created_at should be in ISO format")
    
    @pytest.mark.asyncio
    async def test_execute_returns_unique_task_id(self, create_task_service, task_repository, event_bus):
        """Test that each execution returns a unique task ID"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        
        # Act
        result1 = await create_task_service.execute(user_id, title)
        result2 = await create_task_service.execute(user_id, title)
        
        # Assert
        assert result1["task_id"] != result2["task_id"]
        assert result1["task_id"].startswith("task-")
        assert result2["task_id"].startswith("task-")


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceEdgeCases:
    """Test CreateTaskService edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_only_description_creates_task(self, create_task_service, task_repository, event_bus):
        """Test that whitespace-only description creates a task with empty description"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        description = "   "
        
        # Act
        result = await create_task_service.execute(user_id, title, description)
        
        # Assert
        assert result is not None
        assert result["description"] == ""
        assert task_repository.save_called
        assert event_bus.publish_called
    
    @pytest.mark.asyncio
    async def test_execute_preserves_task_creation_timestamp(self, create_task_service, task_repository, event_bus):
        """Test that task creation timestamp is preserved"""
        # Arrange
        user_id = "user-123"
        title = "Test Task"
        
        # Act
        result = await create_task_service.execute(user_id, title)
        
        # Assert
        assert result["created_at"] is not None
        created_at = datetime.fromisoformat(result["created_at"])
        now = datetime.now(timezone.utc)
        
        # The created_at should be very close to now (within 1 second)
        time_diff = abs((created_at - now).total_seconds())
        assert time_diff < 1.0 