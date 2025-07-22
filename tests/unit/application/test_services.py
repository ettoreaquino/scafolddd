import pytest
from datetime import datetime, timezone
from src.application.services.complete_task import CompleteTaskService
from src.application.services.create_task import CreateTaskService
from src.application.services.get_task import GetTaskService
from src.application.services.list_tasks import ListTasksService
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
        self.find_by_id_calls = []
        self.find_by_user_id_calls = []
    
    async def find_by_id(self, task_id) -> Task:
        """Mock find_by_id method"""
        self.find_by_id_calls.append(task_id)
        return self.tasks.get(str(task_id))
    
    async def find_by_user_id(self, user_id) -> list[Task]:
        """Mock find_by_user_id method"""
        self.find_by_user_id_calls.append(user_id)
        return [task for task in self.tasks.values() if task.user_id == user_id]
    
    async def save(self, task: Task) -> None:
        """Mock save method"""
        self.save_called = True
        self.tasks[str(task.id)] = task


# Test Constants
TASK_ID_1 = "task-123"
TASK_ID_2 = "task-456"
TASK_ID_3 = "task-789"
TASK_ID_4 = "task-999"
USER_ID_1 = "user-123"
USER_ID_2 = "user-456"
TASK_TITLE = "Test Task"
TASK_DESCRIPTION = "A test task for completion testing"
IN_PROGRESS_TITLE = "In Progress Task"
IN_PROGRESS_DESCRIPTION = "A task that's in progress"
COMPLETED_TITLE = "Completed Task"
COMPLETED_DESCRIPTION = "A task that's already completed"
CANCELLED_TITLE = "Cancelled Task"
CANCELLED_DESCRIPTION = "A task that's been cancelled"


def create_task_with_status(
    task_id: str,
    user_id: str,
    title: str,
    description: str,
    status: TaskStatus,
    completed_at: datetime = None
) -> Task:
    """Helper function to create tasks with specific status"""
    now = datetime.now(timezone.utc)
    return Task(
        id=TaskId(task_id),
        user_id=UserId(user_id),
        title=title,
        description=description,
        status=status,
        created_at=now,
        updated_at=now,
        completed_at=completed_at
    )


def assert_task_data_structure(result: dict, task: Task):
    """Helper function to assert task data structure"""
    assert result["task_id"] == str(task.id)
    assert result["title"] == task.title
    assert result["status"] == str(task.status)
    
    # Optional fields that may not be present in all services
    if "description" in result:
        assert result["description"] == task.description
    if "user_id" in result:
        assert result["user_id"] == str(task.user_id)
    if "created_at" in result:
        assert result["created_at"] == task.created_at.isoformat()
    if "updated_at" in result:
        if task.updated_at:
            assert result["updated_at"] == task.updated_at.isoformat()
        else:
            assert result["updated_at"] is None
    if "completed_at" in result:
        if task.completed_at:
            assert result["completed_at"] == task.completed_at.isoformat()
        else:
            assert result["completed_at"] is None


def assert_events_published(event_bus: MockEventBus, expected_event_types: list):
    """Helper function to assert events were published"""
    assert event_bus.publish_called
    assert len(event_bus.published_events) == len(expected_event_types)
    
    event_types = [type(event) for event in event_bus.published_events]
    for expected_type in expected_event_types:
        assert expected_type in event_types


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
def get_task_service(task_repository):
    """Create a GetTaskService instance with mocked dependencies"""
    return GetTaskService(task_repository)


@pytest.fixture
def list_tasks_service(task_repository):
    """Create a ListTasksService instance with mocked dependencies"""
    return ListTasksService(task_repository)


@pytest.fixture
def list_tasks_service(task_repository):
    """Create a ListTasksService instance with mocked dependencies"""
    return ListTasksService(task_repository)


@pytest.fixture
def pending_task():
    """Create a pending task for testing"""
    return create_task_with_status(
        TASK_ID_1, USER_ID_2, TASK_TITLE, TASK_DESCRIPTION, TaskStatus.PENDING
    )


@pytest.fixture
def in_progress_task():
    """Create an in-progress task for testing"""
    return create_task_with_status(
        TASK_ID_2, USER_ID_2, IN_PROGRESS_TITLE, IN_PROGRESS_DESCRIPTION, TaskStatus.IN_PROGRESS
    )


@pytest.fixture
def completed_task():
    """Create a completed task for testing"""
    now = datetime.now(timezone.utc)
    return create_task_with_status(
        TASK_ID_3, USER_ID_2, COMPLETED_TITLE, COMPLETED_DESCRIPTION, 
        TaskStatus.COMPLETED, completed_at=now
    )


@pytest.fixture
def cancelled_task():
    """Create a cancelled task for testing"""
    return create_task_with_status(
        TASK_ID_4, USER_ID_2, CANCELLED_TITLE, CANCELLED_DESCRIPTION, TaskStatus.CANCELLED
    )


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceInitialization:
    """Test CompleteTaskService initialization and dependency injection"""
    
    def test_service_initialization_with_dependencies(self, task_repository, event_bus):
        """Test that service can be initialized with dependencies"""
        service = CompleteTaskService(task_repository, event_bus)
        
        assert service._task_repository == task_repository
        assert service._event_bus == event_bus


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceInputValidation:
    """Test input validation in CompleteTaskService"""
    
    @pytest.mark.asyncio
    async def test_execute_with_none_task_id_raises_error(self, complete_task_service):
        """Test that None task_id raises ValueError"""
        with pytest.raises(ValueError, match="Task ID is required"):
            await complete_task_service.execute(None)
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_task_id_raises_error(self, complete_task_service):
        """Test that empty task_id raises ValueError"""
        with pytest.raises(ValueError, match="Task ID is required"):
            await complete_task_service.execute("")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_task_id_raises_error(self, complete_task_service):
        """Test that whitespace-only task_id raises ValueError"""
        with pytest.raises(ValueError, match="Task ID is required"):
            await complete_task_service.execute("   ")
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_task_id_does_not_raise_error(self, complete_task_service, task_repository, pending_task):
        """Test that valid task_id doesn't raise validation error"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await complete_task_service.execute(str(pending_task.id))
        assert result is not None


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceTaskNotFound:
    """Test CompleteTaskService behavior when task is not found"""
    
    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_task_returns_none(self, complete_task_service, task_repository):
        """Test that nonexistent task returns None"""
        result = await complete_task_service.execute("nonexistent-task")
        assert result is None


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceBusinessRules:
    """Test CompleteTaskService business rule validation"""
    
    @pytest.mark.asyncio
    async def test_execute_with_completed_task_raises_error(self, complete_task_service, task_repository, completed_task):
        """Test that completed task raises error"""
        task_repository.tasks[str(completed_task.id)] = completed_task
        
        with pytest.raises(ValueError, match="Task with status 'completed' cannot be completed"):
            await complete_task_service.execute(str(completed_task.id))
    
    @pytest.mark.asyncio
    async def test_execute_with_cancelled_task_raises_error(self, complete_task_service, task_repository, cancelled_task):
        """Test that cancelled task raises error"""
        task_repository.tasks[str(cancelled_task.id)] = cancelled_task
        
        with pytest.raises(ValueError, match="Task with status 'cancelled' cannot be completed"):
            await complete_task_service.execute(str(cancelled_task.id))


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceSuccessfulCompletion:
    """Test CompleteTaskService successful completion scenarios"""
    
    @pytest.mark.asyncio
    async def test_execute_with_pending_task_completes_successfully(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that pending task can be completed successfully"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await complete_task_service.execute(str(pending_task.id))
        
        assert result is not None
        assert result["status"] == str(TaskStatus.COMPLETED)
        assert result["completed_at"] is not None
        
        assert pending_task.status == TaskStatus.COMPLETED
        assert pending_task.updated_at is not None
        assert task_repository.save_called
        
        # Pending task should publish TaskCreated, TaskStatusChanged and TaskCompleted events
        assert_events_published(event_bus, [TaskCreated, TaskStatusChanged, TaskCompleted])
    
    @pytest.mark.asyncio
    async def test_execute_with_in_progress_task_completes_successfully(self, complete_task_service, task_repository, event_bus, in_progress_task):
        """Test that in-progress task can be completed successfully"""
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        
        result = await complete_task_service.execute(str(in_progress_task.id))
        
        assert result is not None
        assert result["status"] == str(TaskStatus.COMPLETED)
        assert result["completed_at"] is not None
        
        assert in_progress_task.status == TaskStatus.COMPLETED
        assert in_progress_task.updated_at is not None
        assert task_repository.save_called
        
        assert_events_published(event_bus, [TaskStatusChanged, TaskCompleted])
    
    @pytest.mark.asyncio
    async def test_execute_trims_whitespace_from_task_id(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that task_id whitespace is trimmed before processing"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_id_with_whitespace = f"  {str(pending_task.id)}  "
        
        result = await complete_task_service.execute(task_id_with_whitespace)
        
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
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        await complete_task_service.execute(str(pending_task.id))
        
        # Pending task should publish TaskCreated, TaskStatusChanged and TaskCompleted events
        assert_events_published(event_bus, [TaskCreated, TaskStatusChanged, TaskCompleted])
        
        status_changed_event = next(
            (event for event in event_bus.published_events if isinstance(event, TaskStatusChanged)), 
            None
        )
        assert status_changed_event is not None
        assert status_changed_event.aggregate_id == str(pending_task.id)
        assert status_changed_event.old_status == str(TaskStatus.PENDING)
        assert status_changed_event.new_status == str(TaskStatus.COMPLETED)
        
        completed_event = next(
            (event for event in event_bus.published_events if isinstance(event, TaskCompleted)), 
            None
        )
        assert completed_event is not None
        assert completed_event.aggregate_id == str(pending_task.id)
    
    @pytest.mark.asyncio
    async def test_execute_clears_events_after_publishing(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that events are cleared after publishing"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        await complete_task_service.execute(str(pending_task.id))
        
        assert event_bus.publish_called
        assert len(pending_task._events) == 0


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceRepositoryInteraction:
    """Test CompleteTaskService repository interaction"""
    
    @pytest.mark.asyncio
    async def test_execute_calls_repository_methods_in_correct_order(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that repository methods are called in correct order"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        await complete_task_service.execute(str(pending_task.id))
        
        assert len(task_repository.find_by_id_calls) == 1
        assert task_repository.find_by_id_calls[0].value == str(pending_task.id)
        assert task_repository.save_called
    
    @pytest.mark.asyncio
    async def test_execute_saves_updated_task(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that updated task is saved to repository"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        original_updated_at = pending_task.updated_at
        
        await complete_task_service.execute(str(pending_task.id))
        
        assert task_repository.save_called
        assert pending_task.updated_at > original_updated_at
        assert pending_task.status == TaskStatus.COMPLETED


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceReturnValue:
    """Test CompleteTaskService return value structure"""
    
    @pytest.mark.asyncio
    async def test_execute_returns_correct_data_structure(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that execute returns correct data structure"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await complete_task_service.execute(str(pending_task.id))
        
        assert result is not None
        assert_task_data_structure(result, pending_task)
        assert result["status"] == str(TaskStatus.COMPLETED)
        assert result["completed_at"] is not None
    
    @pytest.mark.asyncio
    async def test_execute_returns_iso_format_completed_at(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that completed_at is returned in ISO format"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await complete_task_service.execute(str(pending_task.id))
        
        assert result["completed_at"] is not None
        try:
            datetime.fromisoformat(result["completed_at"])
        except ValueError:
            pytest.fail("completed_at should be in ISO format")


@pytest.mark.application
@pytest.mark.unit
class TestCompleteTaskServiceEdgeCases:
    """Test CompleteTaskService edge cases"""
    
    @pytest.mark.asyncio
    async def test_execute_with_task_that_has_no_events(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that task without events handles correctly"""
        pending_task._events = []
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await complete_task_service.execute(str(pending_task.id))
        
        assert result is not None
        assert event_bus.publish_called
        assert len(event_bus.published_events) == 2  # TaskStatusChanged + TaskCompleted
    
    @pytest.mark.asyncio
    async def test_execute_preserves_task_other_properties(self, complete_task_service, task_repository, event_bus, pending_task):
        """Test that other task properties are preserved during completion"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        original_title = pending_task.title
        original_description = pending_task.description
        original_user_id = pending_task.user_id
        
        result = await complete_task_service.execute(str(pending_task.id))
        
        assert result is not None
        assert pending_task.title == original_title
        assert pending_task.description == original_description
        assert pending_task.user_id == original_user_id
        assert result["title"] == original_title
        # CompleteTaskService doesn't return description or user_id


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceInitialization:
    """Test CreateTaskService initialization and dependency injection"""
    
    def test_service_initialization_with_dependencies(self, task_repository, event_bus):
        """Test that service can be initialized with dependencies"""
        service = CreateTaskService(task_repository, event_bus)
        
        assert service._task_repository == task_repository
        assert service._event_bus == event_bus


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceInputValidation:
    """Test input validation in CreateTaskService"""
    
    @pytest.mark.asyncio
    async def test_execute_with_none_user_id_raises_error(self, create_task_service):
        """Test that None user_id raises ValueError"""
        with pytest.raises(ValueError, match="User ID is required"):
            await create_task_service.execute(None, "Test Title")
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_user_id_raises_error(self, create_task_service):
        """Test that empty user_id raises ValueError"""
        with pytest.raises(ValueError, match="User ID is required"):
            await create_task_service.execute("", "Test Title")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_user_id_raises_error(self, create_task_service):
        """Test that whitespace-only user_id raises ValueError"""
        with pytest.raises(ValueError, match="User ID is required"):
            await create_task_service.execute("   ", "Test Title")
    
    @pytest.mark.asyncio
    async def test_execute_with_none_title_raises_error(self, create_task_service):
        """Test that None title raises ValueError"""
        with pytest.raises(ValueError, match="Task title is required"):
            await create_task_service.execute("user-123", None)
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_title_raises_error(self, create_task_service):
        """Test that empty title raises ValueError"""
        with pytest.raises(ValueError, match="Task title is required"):
            await create_task_service.execute("user-123", "")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_title_raises_error(self, create_task_service):
        """Test that whitespace-only title raises ValueError"""
        with pytest.raises(ValueError, match="Task title is required"):
            await create_task_service.execute("user-123", "   ")
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_inputs_does_not_raise_error(self, create_task_service, task_repository, event_bus):
        """Test that valid inputs don't raise validation error"""
        try:
            result = await create_task_service.execute("user-123", "Test Title")
            assert result is not None
        except ValueError:
            pytest.fail("Valid inputs should not raise ValueError")


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceSuccessfulCreation:
    """Test CreateTaskService successful creation scenarios"""
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_inputs_creates_task_successfully(self, create_task_service, task_repository, event_bus):
        """Test that valid inputs create task successfully"""
        result = await create_task_service.execute("user-123", "Test Title", "Test Description")
        
        assert result is not None
        assert result["title"] == "Test Title"
        assert result["description"] == "Test Description"
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == "user-123"
        assert result["created_at"] is not None
        
        assert task_repository.save_called
        assert event_bus.publish_called
        assert_events_published(event_bus, [TaskCreated])
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_description_creates_task_successfully(self, create_task_service, task_repository, event_bus):
        """Test that empty description creates task successfully"""
        result = await create_task_service.execute("user-123", "Test Title", "")
        
        assert result is not None
        assert result["title"] == "Test Title"
        assert result["description"] == ""
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == "user-123"
        
        assert task_repository.save_called
        assert event_bus.publish_called
        assert_events_published(event_bus, [TaskCreated])
    
    @pytest.mark.asyncio
    async def test_execute_with_none_description_creates_task_successfully(self, create_task_service, task_repository, event_bus):
        """Test that None description creates task successfully"""
        result = await create_task_service.execute("user-123", "Test Title", None)
        
        assert result is not None
        assert result["title"] == "Test Title"
        assert result["description"] == ""
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == "user-123"
        
        assert task_repository.save_called
        assert event_bus.publish_called
        assert_events_published(event_bus, [TaskCreated])
    
    @pytest.mark.asyncio
    async def test_execute_trims_whitespace_from_inputs(self, create_task_service, task_repository, event_bus):
        """Test that whitespace is trimmed from inputs"""
        result = await create_task_service.execute("  user-123  ", "  Test Title  ", "  Test Description  ")
        
        assert result is not None
        assert result["title"] == "Test Title"
        assert result["description"] == "Test Description"
        assert result["user_id"] == "user-123"
        
        assert task_repository.save_called
        assert event_bus.publish_called


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceEventPublishing:
    """Test CreateTaskService event publishing behavior"""
    
    @pytest.mark.asyncio
    async def test_execute_publishes_task_created_event(self, create_task_service, task_repository, event_bus):
        """Test that TaskCreated event is published when creating a task"""
        result = await create_task_service.execute("user-123", "Test Title", "Test Description")
        
        assert event_bus.publish_called
        assert_events_published(event_bus, [TaskCreated])
        
        created_event = next(
            (event for event in event_bus.published_events if isinstance(event, TaskCreated)), 
            None
        )
        assert created_event is not None
        assert created_event.aggregate_id == result["task_id"]
        assert created_event.task_title == "Test Title"
    
    @pytest.mark.asyncio
    async def test_execute_clears_events_after_publishing(self, create_task_service, task_repository, event_bus):
        """Test that events are cleared after publishing"""
        result = await create_task_service.execute("user-123", "Test Title")
        
        assert event_bus.publish_called
        # The task should have no events after publishing
        saved_task = task_repository.tasks[result["task_id"]]
        assert len(saved_task._events) == 0


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceRepositoryInteraction:
    """Test CreateTaskService repository interaction"""
    
    @pytest.mark.asyncio
    async def test_execute_saves_task_to_repository(self, create_task_service, task_repository, event_bus):
        """Test that created task is saved to repository"""
        result = await create_task_service.execute("user-123", "Test Title", "Test Description")
        
        assert task_repository.save_called
        assert result["task_id"] in task_repository.tasks
        
        saved_task = task_repository.tasks[result["task_id"]]
        assert saved_task.title == "Test Title"
        assert saved_task.description == "Test Description"
        assert saved_task.status == TaskStatus.PENDING
        assert saved_task.user_id == UserId("user-123")


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceReturnValue:
    """Test CreateTaskService return value structure"""
    
    @pytest.mark.asyncio
    async def test_execute_returns_correct_data_structure(self, create_task_service, task_repository, event_bus):
        """Test that execute returns correct data structure"""
        result = await create_task_service.execute("user-123", "Test Title", "Test Description")
        
        assert result is not None
        assert "task_id" in result
        assert "title" in result
        assert "description" in result
        assert "status" in result
        assert "user_id" in result
        assert "created_at" in result
        
        assert result["title"] == "Test Title"
        assert result["description"] == "Test Description"
        assert result["status"] == str(TaskStatus.PENDING)
        assert result["user_id"] == "user-123"
    
    @pytest.mark.asyncio
    async def test_execute_returns_iso_format_created_at(self, create_task_service, task_repository, event_bus):
        """Test that created_at is returned in ISO format"""
        result = await create_task_service.execute("user-123", "Test Title")
        
        assert result["created_at"] is not None
        try:
            datetime.fromisoformat(result["created_at"])
        except ValueError:
            pytest.fail("created_at should be in ISO format")
    
    @pytest.mark.asyncio
    async def test_execute_returns_unique_task_id(self, create_task_service, task_repository, event_bus):
        """Test that unique task IDs are generated"""
        result1 = await create_task_service.execute("user-123", "Test Title 1")
        result2 = await create_task_service.execute("user-123", "Test Title 2")
        
        assert result1["task_id"] != result2["task_id"]
        assert result1["task_id"] in task_repository.tasks
        assert result2["task_id"] in task_repository.tasks


@pytest.mark.application
@pytest.mark.unit
class TestCreateTaskServiceEdgeCases:
    """Test CreateTaskService edge cases"""
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_only_description_creates_task(self, create_task_service, task_repository, event_bus):
        """Test that whitespace-only description creates task"""
        result = await create_task_service.execute("user-123", "Test Title", "   ")
        
        assert result is not None
        assert result["title"] == "Test Title"
        assert result["description"] == ""
        assert result["status"] == str(TaskStatus.PENDING)
        
        assert task_repository.save_called
        assert event_bus.publish_called
    
    @pytest.mark.asyncio
    async def test_execute_preserves_task_creation_timestamp(self, create_task_service, task_repository, event_bus):
        """Test that task creation timestamp is preserved"""
        result = await create_task_service.execute("user-123", "Test Title")
        
        assert result["created_at"] is not None
        
        saved_task = task_repository.tasks[result["task_id"]]
        assert saved_task.created_at.isoformat() == result["created_at"]


@pytest.mark.application
@pytest.mark.unit
class TestGetTaskServiceInitialization:
    """Test GetTaskService initialization and dependency injection"""
    
    def test_service_initialization_with_dependencies(self, task_repository):
        """Test that service can be initialized with dependencies"""
        service = GetTaskService(task_repository)
        
        assert service._task_repository == task_repository


@pytest.mark.application
@pytest.mark.unit
class TestGetTaskServiceInputValidation:
    """Test input validation in GetTaskService"""
    
    @pytest.mark.asyncio
    async def test_execute_with_none_task_id_raises_error(self, get_task_service):
        """Test that None task_id raises ValueError"""
        with pytest.raises(ValueError, match="Task ID is required"):
            await get_task_service.execute(None)
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_task_id_raises_error(self, get_task_service):
        """Test that empty task_id raises ValueError"""
        with pytest.raises(ValueError, match="Task ID is required"):
            await get_task_service.execute("")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_task_id_raises_error(self, get_task_service):
        """Test that whitespace-only task_id raises ValueError"""
        with pytest.raises(ValueError, match="Task ID is required"):
            await get_task_service.execute("   ")
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_task_id_does_not_raise_error(self, get_task_service, task_repository):
        """Test that valid task_id doesn't raise validation error"""
        try:
            result = await get_task_service.execute("task-123")
            assert result is None  # Task doesn't exist, but no error
        except ValueError:
            pytest.fail("Valid task_id should not raise ValueError")


@pytest.mark.application
@pytest.mark.unit
class TestGetTaskServiceTaskNotFound:
    """Test GetTaskService behavior when task is not found"""
    
    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_task_returns_none(self, get_task_service, task_repository):
        """Test that nonexistent task returns None"""
        result = await get_task_service.execute("nonexistent-task")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_task_calls_repository_with_trimmed_id(self, get_task_service, task_repository):
        """Test that repository is called with trimmed task ID"""
        await get_task_service.execute("  task-123  ")
        
        assert len(task_repository.find_by_id_calls) == 1
        assert task_repository.find_by_id_calls[0].value == "task-123"


@pytest.mark.application
@pytest.mark.unit
class TestGetTaskServiceSuccessfulRetrieval:
    """Test GetTaskService successful retrieval scenarios"""
    
    @pytest.mark.asyncio
    async def test_execute_with_existing_task_returns_task_data(self, get_task_service, task_repository, pending_task):
        """Test that existing task returns task data"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await get_task_service.execute(str(pending_task.id))
        
        assert result is not None
        assert_task_data_structure(result, pending_task)
    
    @pytest.mark.asyncio
    async def test_execute_with_completed_task_returns_completed_at(self, get_task_service, task_repository, completed_task):
        """Test that completed task returns completed_at"""
        task_repository.tasks[str(completed_task.id)] = completed_task
        
        result = await get_task_service.execute(str(completed_task.id))
        
        assert result is not None
        assert result["completed_at"] is not None
        assert result["status"] == str(TaskStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_execute_trims_whitespace_from_task_id(self, get_task_service, task_repository, pending_task):
        """Test that task_id whitespace is trimmed before processing"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_id_with_whitespace = f"  {str(pending_task.id)}  "
        
        result = await get_task_service.execute(task_id_with_whitespace)
        
        assert result is not None
        assert result["task_id"] == str(pending_task.id)


@pytest.mark.application
@pytest.mark.unit
class TestGetTaskServiceRepositoryInteraction:
    """Test GetTaskService repository interaction"""
    
    @pytest.mark.asyncio
    async def test_execute_calls_repository_with_task_id(self, get_task_service, task_repository, pending_task):
        """Test that repository is called with task ID"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        await get_task_service.execute(str(pending_task.id))
        
        assert len(task_repository.find_by_id_calls) == 1
        assert task_repository.find_by_id_calls[0].value == str(pending_task.id)
    
    @pytest.mark.asyncio
    async def test_execute_calls_repository_only_once(self, get_task_service, task_repository, pending_task):
        """Test that repository is called only once"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        await get_task_service.execute(str(pending_task.id))
        
        assert len(task_repository.find_by_id_calls) == 1


@pytest.mark.application
@pytest.mark.unit
class TestGetTaskServiceReturnValue:
    """Test GetTaskService return value structure"""
    
    @pytest.mark.asyncio
    async def test_execute_returns_correct_data_structure(self, get_task_service, task_repository, pending_task):
        """Test that execute returns correct data structure"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await get_task_service.execute(str(pending_task.id))
        
        assert result is not None
        assert_task_data_structure(result, pending_task)
    
    @pytest.mark.asyncio
    async def test_execute_returns_iso_format_timestamps(self, get_task_service, task_repository, completed_task):
        """Test that timestamps are returned in ISO format"""
        task_repository.tasks[str(completed_task.id)] = completed_task
        
        result = await get_task_service.execute(str(completed_task.id))
        
        assert result["created_at"] is not None
        assert result["updated_at"] is not None
        assert result["completed_at"] is not None
        
        try:
            datetime.fromisoformat(result["created_at"])
            datetime.fromisoformat(result["updated_at"])
            datetime.fromisoformat(result["completed_at"])
        except ValueError:
            pytest.fail("Timestamps should be in ISO format")
    
    @pytest.mark.asyncio
    async def test_execute_returns_none_for_missing_timestamps(self, get_task_service, task_repository, pending_task):
        """Test that missing timestamps return None"""
        task_without_timestamps = create_task_with_status(
            TASK_ID_1, USER_ID_1, TASK_TITLE, TASK_DESCRIPTION, TaskStatus.PENDING
        )
        task_without_timestamps.updated_at = None
        task_without_timestamps.completed_at = None
        task_repository.tasks[str(task_without_timestamps.id)] = task_without_timestamps
        
        result = await get_task_service.execute(str(task_without_timestamps.id))
        
        assert result["updated_at"] is None
        assert result["completed_at"] is None
        assert result["created_at"] is not None


@pytest.mark.application
@pytest.mark.unit
class TestGetTaskServiceEdgeCases:
    """Test GetTaskService edge cases"""
    
    @pytest.mark.asyncio
    async def test_execute_with_task_that_has_no_updated_at(self, get_task_service, task_repository):
        """Test that task without updated_at handles correctly"""
        task_without_updated_at = create_task_with_status(
            TASK_ID_1, USER_ID_1, TASK_TITLE, TASK_DESCRIPTION, TaskStatus.PENDING
        )
        task_without_updated_at.updated_at = None
        task_repository.tasks[str(task_without_updated_at.id)] = task_without_updated_at
        
        result = await get_task_service.execute(str(task_without_updated_at.id))
        
        assert result is not None
        assert result["updated_at"] is None
        assert result["completed_at"] is None
        assert result["created_at"] is not None
    
    @pytest.mark.asyncio
    async def test_execute_with_task_that_has_no_completed_at(self, get_task_service, task_repository, pending_task):
        """Test that task without completed_at handles correctly"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        result = await get_task_service.execute(str(pending_task.id))
        
        assert result is not None
        assert result["completed_at"] is None
        assert result["status"] == str(TaskStatus.PENDING)
    
    @pytest.mark.asyncio
    async def test_execute_preserves_all_task_properties(self, get_task_service, task_repository, in_progress_task):
        """Test that all task properties are preserved in the response"""
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        
        result = await get_task_service.execute(str(in_progress_task.id))
        
        assert result is not None
        assert_task_data_structure(result, in_progress_task) 


@pytest.mark.application
@pytest.mark.unit
class TestListTasksServiceInitialization:
    """Test ListTasksService initialization and dependency injection"""
    
    def test_service_initialization_with_dependencies(self, task_repository):
        """Test that service can be initialized with dependencies"""
        service = ListTasksService(task_repository)
        
        assert service._task_repository == task_repository


@pytest.mark.application
@pytest.mark.unit
class TestListTasksServiceInputValidation:
    """Test input validation in ListTasksService"""
    
    @pytest.mark.asyncio
    async def test_execute_with_none_user_id_raises_error(self, list_tasks_service):
        """Test that None user_id raises ValueError"""
        with pytest.raises(ValueError, match="User ID is required"):
            await list_tasks_service.execute(None)
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_user_id_raises_error(self, list_tasks_service):
        """Test that empty user_id raises ValueError"""
        with pytest.raises(ValueError, match="User ID is required"):
            await list_tasks_service.execute("")
    
    @pytest.mark.asyncio
    async def test_execute_with_whitespace_user_id_raises_error(self, list_tasks_service):
        """Test that whitespace-only user_id raises ValueError"""
        with pytest.raises(ValueError, match="User ID is required"):
            await list_tasks_service.execute("   ")
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_user_id_does_not_raise_error(self, list_tasks_service, task_repository):
        """Test that valid user_id doesn't raise validation error"""
        try:
            result = await list_tasks_service.execute("user-123")
            assert isinstance(result, list)
        except ValueError:
            pytest.fail("Valid user_id should not raise ValueError")


@pytest.mark.application
@pytest.mark.unit
class TestListTasksServiceSuccessfulRetrieval:
    """Test ListTasksService successful retrieval scenarios"""
    
    @pytest.mark.asyncio
    async def test_execute_with_user_with_tasks_returns_task_list(self, list_tasks_service, task_repository, pending_task, in_progress_task):
        """Test that user with tasks returns list of tasks"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        
        result = await list_tasks_service.execute(str(pending_task.user_id))
        
        assert isinstance(result, list)
        assert len(result) == 2
        
        task_ids = [task["task_id"] for task in result]
        assert str(pending_task.id) in task_ids
        assert str(in_progress_task.id) in task_ids
    
    @pytest.mark.asyncio
    async def test_execute_with_user_with_no_tasks_returns_empty_list(self, list_tasks_service, task_repository):
        """Test that user with no tasks returns empty list"""
        result = await list_tasks_service.execute("user-with-no-tasks")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_execute_returns_correct_data_structure_for_each_task(self, list_tasks_service, task_repository, pending_task, completed_task):
        """Test that each task in the list has correct data structure"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_repository.tasks[str(completed_task.id)] = completed_task
        
        result = await list_tasks_service.execute(str(pending_task.user_id))
        
        assert len(result) == 2
        
        for task_data in result:
            assert "task_id" in task_data
            assert "title" in task_data
            assert "description" in task_data
            assert "status" in task_data
            assert "created_at" in task_data
            assert "updated_at" in task_data
            assert "completed_at" in task_data
            assert "user_id" in task_data
    
    @pytest.mark.asyncio
    async def test_execute_trims_whitespace_from_user_id(self, list_tasks_service, task_repository, pending_task):
        """Test that user_id whitespace is trimmed before processing"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        user_id_with_whitespace = f"  {str(pending_task.user_id)}  "
        
        result = await list_tasks_service.execute(user_id_with_whitespace)
        
        assert len(result) == 1
        assert result[0]["task_id"] == str(pending_task.id)


@pytest.mark.application
@pytest.mark.unit
class TestListTasksServiceRepositoryInteraction:
    """Test ListTasksService repository interaction"""
    
    @pytest.mark.asyncio
    async def test_execute_calls_repository_with_user_id(self, list_tasks_service, task_repository, pending_task):
        """Test that repository is called with user ID"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        await list_tasks_service.execute(str(pending_task.user_id))
        
        assert len(task_repository.find_by_user_id_calls) == 1
        assert task_repository.find_by_user_id_calls[0] == UserId(str(pending_task.user_id))
    
    @pytest.mark.asyncio
    async def test_execute_calls_repository_only_once(self, list_tasks_service, task_repository, pending_task):
        """Test that repository is called only once"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        
        await list_tasks_service.execute(str(pending_task.user_id))
        
        assert len(task_repository.find_by_user_id_calls) == 1


@pytest.mark.application
@pytest.mark.unit
class TestListTasksServiceReturnValue:
    """Test ListTasksService return value structure"""
    
    @pytest.mark.asyncio
    async def test_execute_returns_list_of_task_data(self, list_tasks_service, task_repository, pending_task, in_progress_task, completed_task):
        """Test that execute returns list of task data"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        task_repository.tasks[str(completed_task.id)] = completed_task
        
        result = await list_tasks_service.execute(str(pending_task.user_id))
        
        assert isinstance(result, list)
        assert len(result) == 3
        
        # Create a mapping of task IDs to tasks for validation
        tasks_map = {
            str(pending_task.id): pending_task,
            str(in_progress_task.id): in_progress_task,
            str(completed_task.id): completed_task
        }
        
        for task_data in result:
            task_id = task_data["task_id"]
            assert task_id in tasks_map, f"Task ID {task_id} not found in expected tasks"
            assert_task_data_structure(task_data, tasks_map[task_id])
    
    @pytest.mark.asyncio
    async def test_execute_returns_iso_format_timestamps(self, list_tasks_service, task_repository, completed_task):
        """Test that timestamps are returned in ISO format"""
        task_repository.tasks[str(completed_task.id)] = completed_task
        
        result = await list_tasks_service.execute(str(completed_task.user_id))
        
        assert len(result) == 1
        task_data = result[0]
        
        assert task_data["created_at"] is not None
        assert task_data["updated_at"] is not None
        assert task_data["completed_at"] is not None
        
        try:
            datetime.fromisoformat(task_data["created_at"])
            datetime.fromisoformat(task_data["updated_at"])
            datetime.fromisoformat(task_data["completed_at"])
        except ValueError:
            pytest.fail("Timestamps should be in ISO format")
    
    @pytest.mark.asyncio
    async def test_execute_returns_none_for_missing_timestamps(self, list_tasks_service, task_repository):
        """Test that missing timestamps return None"""
        task_without_timestamps = create_task_with_status(
            TASK_ID_1, USER_ID_1, TASK_TITLE, TASK_DESCRIPTION, TaskStatus.PENDING
        )
        task_without_timestamps.updated_at = None
        task_without_timestamps.completed_at = None
        task_repository.tasks[str(task_without_timestamps.id)] = task_without_timestamps
        
        result = await list_tasks_service.execute(str(task_without_timestamps.user_id))
        
        assert len(result) == 1
        task_data = result[0]
        assert task_data["updated_at"] is None
        assert task_data["completed_at"] is None
        assert task_data["created_at"] is not None


@pytest.mark.application
@pytest.mark.unit
class TestListTasksServiceEdgeCases:
    """Test ListTasksService edge cases"""
    
    @pytest.mark.asyncio
    async def test_execute_with_multiple_users_returns_only_user_tasks(self, list_tasks_service, task_repository):
        """Test that only tasks for the specified user are returned"""
        user1_task = create_task_with_status(TASK_ID_1, USER_ID_1, "User 1 Task", "Description", TaskStatus.PENDING)
        user2_task = create_task_with_status(TASK_ID_2, USER_ID_2, "User 2 Task", "Description", TaskStatus.PENDING)
        
        task_repository.tasks[str(user1_task.id)] = user1_task
        task_repository.tasks[str(user2_task.id)] = user2_task
        
        result = await list_tasks_service.execute(USER_ID_1)
        
        assert len(result) == 1
        assert result[0]["task_id"] == str(user1_task.id)
        assert result[0]["user_id"] == USER_ID_1
    
    @pytest.mark.asyncio
    async def test_execute_with_tasks_in_different_statuses(self, list_tasks_service, task_repository, pending_task, in_progress_task, completed_task, cancelled_task):
        """Test that tasks in different statuses are all returned"""
        task_repository.tasks[str(pending_task.id)] = pending_task
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        task_repository.tasks[str(completed_task.id)] = completed_task
        task_repository.tasks[str(cancelled_task.id)] = cancelled_task
        
        result = await list_tasks_service.execute(str(pending_task.user_id))
        
        assert len(result) == 4
        
        statuses = [task["status"] for task in result]
        assert str(TaskStatus.PENDING) in statuses
        assert str(TaskStatus.IN_PROGRESS) in statuses
        assert str(TaskStatus.COMPLETED) in statuses
        assert str(TaskStatus.CANCELLED) in statuses
    
    @pytest.mark.asyncio
    async def test_execute_preserves_all_task_properties(self, list_tasks_service, task_repository, in_progress_task):
        """Test that all task properties are preserved in the response"""
        task_repository.tasks[str(in_progress_task.id)] = in_progress_task
        
        result = await list_tasks_service.execute(str(in_progress_task.user_id))
        
        assert len(result) == 1
        assert_task_data_structure(result[0], in_progress_task) 