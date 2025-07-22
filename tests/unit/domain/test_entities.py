import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus
from src.domain.events import TaskCreated, TaskCompleted, TaskStatusChanged


@pytest.mark.domain
@pytest.mark.unit
class TestTaskCreation:
    """Test Task entity creation and validation"""
    
    def test_task_creation_with_valid_data(self):
        """Test creating a task with valid data"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        title = "Complete project documentation"
        description = "Write comprehensive documentation for the new feature"
        status = TaskStatus.PENDING
        created_at = datetime.now(timezone.utc)
        
        # Act
        task = Task(
            id=task_id,
            user_id=user_id,
            title=title,
            description=description,
            status=status,
            created_at=created_at
        )
        
        # Assert
        assert task.id == task_id
        assert task.user_id == user_id
        assert task.title == title
        assert task.description == description
        assert task.status == status
        assert task.created_at == created_at
        assert task.updated_at is None
        assert task.completed_at is None
    
    def test_task_creation_with_empty_title_raises_error(self):
        """Test that empty title raises ValueError"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        created_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id=task_id,
                user_id=user_id,
                title="",
                description="Some description",
                status=TaskStatus.PENDING,
                created_at=created_at
            )
    
    def test_task_creation_with_whitespace_title_raises_error(self):
        """Test that whitespace-only title raises ValueError"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        created_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id=task_id,
                user_id=user_id,
                title="   ",
                description="Some description",
                status=TaskStatus.PENDING,
                created_at=created_at
            )
    
    def test_task_creation_with_title_too_long_raises_error(self):
        """Test that title exceeding 200 characters raises ValueError"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        created_at = datetime.now(timezone.utc)
        long_title = "a" * 201  # 201 characters
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task title cannot be longer than 200 characters"):
            Task(
                id=task_id,
                user_id=user_id,
                title=long_title,
                description="Some description",
                status=TaskStatus.PENDING,
                created_at=created_at
            )
    
    def test_task_creation_fires_task_created_event(self):
        """Test that task creation fires TaskCreated event for pending tasks"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        title = "Complete project documentation"
        created_at = datetime.now(timezone.utc)
        
        # Act
        task = Task(
            id=task_id,
            user_id=user_id,
            title=title,
            description="Some description",
            status=TaskStatus.PENDING,
            created_at=created_at
        )
        
        # Assert
        events = task.pop_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCreated)
        assert events[0].aggregate_id == str(task_id)
        assert events[0].task_title == title
        assert events[0].user_id == str(user_id)
        assert events[0].timestamp == created_at
    
    def test_task_creation_with_non_pending_status_does_not_fire_event(self):
        """Test that task creation doesn't fire event for non-pending status"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        created_at = datetime.now(timezone.utc)
        
        # Act
        task = Task(
            id=task_id,
            user_id=user_id,
            title="Complete project documentation",
            description="Some description",
            status=TaskStatus.COMPLETED,
            created_at=created_at
        )
        
        # Assert
        events = task.pop_events()
        assert len(events) == 0


@pytest.mark.domain
@pytest.mark.unit
class TestTaskStatusUpdates:
    """Test Task status update functionality"""
    
    def test_update_status_to_different_status(self):
        """Test updating task status to a different status"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Complete project documentation",
            description="Some description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        
        # Act
        with patch('src.domain.entities.task.datetime') as mock_datetime:
            mock_now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = mock_now
            task.update_status(TaskStatus.IN_PROGRESS)
        
        # Assert
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at == mock_now
        
        # Check events
        events = task.pop_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskStatusChanged)
        assert events[0].aggregate_id == str(task.id)
        assert events[0].old_status == str(TaskStatus.PENDING)
        assert events[0].new_status == str(TaskStatus.IN_PROGRESS)
        assert events[0].user_id == str(task.user_id)
        assert events[0].timestamp == mock_now
    
    def test_update_status_to_same_status_does_nothing(self):
        """Test that updating to the same status doesn't change anything"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Complete project documentation",
            description="Some description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        original_updated_at = task.updated_at
        
        # Act
        task.update_status(TaskStatus.PENDING)
        
        # Assert
        assert task.status == TaskStatus.PENDING
        assert task.updated_at == original_updated_at
        
        # No events should be fired
        events = task.pop_events()
        assert len(events) == 0
    
    def test_update_status_to_completed_fires_completion_event(self):
        """Test that updating status to completed fires TaskCompleted event"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Complete project documentation",
            description="Some description",
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        
        # Act
        with patch('src.domain.entities.task.datetime') as mock_datetime:
            mock_now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = mock_now
            task.update_status(TaskStatus.COMPLETED)
        
        # Assert
        assert task.status == TaskStatus.COMPLETED
        assert task.updated_at == mock_now
        
        # Check events - should have both status change and completion events
        events = task.pop_events()
        assert len(events) == 2
        
        # First event should be status change
        assert isinstance(events[0], TaskStatusChanged)
        assert events[0].old_status == str(TaskStatus.IN_PROGRESS)
        assert events[0].new_status == str(TaskStatus.COMPLETED)
        
        # Second event should be completion
        assert isinstance(events[1], TaskCompleted)
        assert events[1].aggregate_id == str(task.id)
        assert events[1].task_title == task.title
        assert events[1].user_id == str(task.user_id)
        assert events[1].timestamp == mock_now


@pytest.mark.domain
@pytest.mark.unit
class TestTaskDetailUpdates:
    """Test Task detail update functionality"""
    
    def test_update_title_only(self):
        """Test updating only the task title"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Old title",
            description="Old description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        
        # Act
        with patch('src.domain.entities.task.datetime') as mock_datetime:
            mock_now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = mock_now
            task.update_details(title="New title")
        
        # Assert
        assert task.title == "New title"
        assert task.description == "Old description"  # Unchanged
        assert task.updated_at == mock_now
    
    def test_update_description_only(self):
        """Test updating only the task description"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Task title",
            description="Old description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        
        # Act
        with patch('src.domain.entities.task.datetime') as mock_datetime:
            mock_now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = mock_now
            task.update_details(description="New description")
        
        # Assert
        assert task.title == "Task title"  # Unchanged
        assert task.description == "New description"
        assert task.updated_at == mock_now
    
    def test_update_both_title_and_description(self):
        """Test updating both title and description"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Old title",
            description="Old description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        
        # Act
        with patch('src.domain.entities.task.datetime') as mock_datetime:
            mock_now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = mock_now
            task.update_details(title="New title", description="New description")
        
        # Assert
        assert task.title == "New title"
        assert task.description == "New description"
        assert task.updated_at == mock_now
    
    def test_update_title_with_empty_string_raises_error(self):
        """Test that updating title to empty string raises ValueError"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Valid title",
            description="Some description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            task.update_details(title="")
    
    def test_update_title_with_whitespace_raises_error(self):
        """Test that updating title to whitespace raises ValueError"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Valid title",
            description="Some description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            task.update_details(title="   ")
    
    def test_update_title_too_long_raises_error(self):
        """Test that updating title to exceed 200 characters raises ValueError"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Valid title",
            description="Some description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        long_title = "a" * 201  # 201 characters
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task title cannot exceed 200 characters"):
            task.update_details(title=long_title)
    
    def test_update_details_with_none_values_does_not_change_fields(self):
        """Test that passing None values doesn't change existing fields"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Original title",
            description="Original description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        original_title = task.title
        original_description = task.description
        
        # Act
        task.update_details(title=None, description=None)
        
        # Assert
        assert task.title == original_title
        assert task.description == original_description
        assert task.updated_at is not None  # Should still update timestamp


@pytest.mark.domain
@pytest.mark.unit
class TestTaskEventManagement:
    """Test Task domain event management"""
    
    def test_pop_events_returns_and_clears_events(self):
        """Test that pop_events returns events and clears the internal list"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act - First pop should return creation event
        events1 = task.pop_events()
        assert len(events1) == 1
        assert isinstance(events1[0], TaskCreated)
        
        # Act - Second pop should return empty list
        events2 = task.pop_events()
        assert len(events2) == 0
    
    def test_multiple_events_accumulate_correctly(self):
        """Test that multiple events accumulate correctly"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        task.pop_events()  # Clear creation event
        
        # Act - Generate multiple events
        task.update_status(TaskStatus.IN_PROGRESS)
        task.update_status(TaskStatus.COMPLETED)
        
        # Assert
        events = task.pop_events()
        assert len(events) == 3  # Status change + Status change + Completion
        
        # Verify event types
        assert isinstance(events[0], TaskStatusChanged)  # PENDING -> IN_PROGRESS
        assert isinstance(events[1], TaskStatusChanged)  # IN_PROGRESS -> COMPLETED
        assert isinstance(events[2], TaskCompleted)      # Completion event


@pytest.mark.domain
@pytest.mark.unit
class TestTaskBusinessLogic:
    """Test Task business logic methods"""
    
    def test_is_completed_returns_true_for_completed_task(self):
        """Test is_completed returns True for completed tasks"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        assert task.is_completed() is True
    
    def test_is_completed_returns_false_for_non_completed_task(self):
        """Test is_completed returns False for non-completed tasks"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        assert task.is_completed() is False
    
    def test_can_be_completed_returns_true_for_pending_task(self):
        """Test can_be_completed returns True for pending tasks"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        assert task.can_be_completed() is True
    
    def test_can_be_completed_returns_true_for_in_progress_task(self):
        """Test can_be_completed returns True for in-progress tasks"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        assert task.can_be_completed() is True
    
    def test_can_be_completed_returns_false_for_completed_task(self):
        """Test can_be_completed returns False for completed tasks"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        assert task.can_be_completed() is False
    
    def test_can_be_completed_returns_false_for_cancelled_task(self):
        """Test can_be_completed returns False for cancelled tasks"""
        # Arrange
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test task",
            description="Test description",
            status=TaskStatus.CANCELLED,
            created_at=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        assert task.can_be_completed() is False


@pytest.mark.domain
@pytest.mark.unit
class TestTaskEdgeCases:
    """Test Task edge cases and boundary conditions"""
    
    def test_task_with_exactly_200_character_title_is_valid(self):
        """Test that task with exactly 200 character title is valid"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        created_at = datetime.now(timezone.utc)
        max_length_title = "a" * 200  # Exactly 200 characters
        
        # Act
        task = Task(
            id=task_id,
            user_id=user_id,
            title=max_length_title,
            description="Some description",
            status=TaskStatus.PENDING,
            created_at=created_at
        )
        
        # Assert
        assert task.title == max_length_title
        assert len(task.title) == 200
    
    def test_task_with_none_description_is_valid(self):
        """Test that task with None description is valid"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        created_at = datetime.now(timezone.utc)
        
        # Act
        task = Task(
            id=task_id,
            user_id=user_id,
            title="Valid title",
            description=None,
            status=TaskStatus.PENDING,
            created_at=created_at
        )
        
        # Assert
        assert task.description is None
    
    def test_task_with_empty_string_description_is_valid(self):
        """Test that task with empty string description is valid"""
        # Arrange
        task_id = TaskId("task-123")
        user_id = UserId("user-456")
        created_at = datetime.now(timezone.utc)
        
        # Act
        task = Task(
            id=task_id,
            user_id=user_id,
            title="Valid title",
            description="",
            status=TaskStatus.PENDING,
            created_at=created_at
        )
        
        # Assert
        assert task.description == ""
    
    def test_task_equality_based_on_all_fields(self):
        """Test that task equality is based on all fields (current dataclass behavior)"""
        # Arrange
        created_at = datetime.now(timezone.utc)
        task1 = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Task 1",
            description="Description 1",
            status=TaskStatus.PENDING,
            created_at=created_at
        )
        
        task2 = Task(
            id=TaskId("task-123"),  # Same ID
            user_id=UserId("user-456"),  # Same user
            title="Task 1",  # Same title
            description="Description 1",  # Same description
            status=TaskStatus.PENDING,  # Same status
            created_at=created_at  # Same timestamp
        )
        
        task3 = Task(
            id=TaskId("task-456"),  # Different ID
            user_id=UserId("user-456"),
            title="Task 1",  # Same title
            description="Description 1",  # Same description
            status=TaskStatus.PENDING,  # Same status
            created_at=created_at
        )
        
        # Clear events to ensure equality comparison works
        task1.pop_events()
        task2.pop_events()
        task3.pop_events()
        
        # Assert
        assert task1 == task2  # All fields are the same
        assert task1 != task3  # Different ID
    
    def test_task_identity_comparison(self):
        """Test that task identity comparison works correctly"""
        # Arrange
        task1 = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Task 1",
            description="Description 1",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        task2 = Task(
            id=TaskId("task-123"),  # Same ID
            user_id=UserId("user-789"),  # Different user
            title="Task 2",  # Different title
            description="Description 2",  # Different description
            status=TaskStatus.COMPLETED,  # Different status
            created_at=datetime.now(timezone.utc)
        )
        
        # Assert - In DDD, entities should be compared by ID, but current implementation compares all fields
        # This test documents the current behavior and highlights a potential improvement
        assert task1.id == task2.id  # Same identity
        assert task1 != task2  # But different objects due to dataclass equality 