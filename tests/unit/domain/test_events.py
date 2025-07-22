import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from src.domain.events import DomainEvent, TaskCreated, TaskCompleted, TaskStatusChanged


@pytest.mark.domain
@pytest.mark.unit
class TestDomainEvent:
    """Test base DomainEvent functionality"""
    
    def test_domain_event_creation_with_all_fields(self):
        """Test creating a domain event with all required fields"""
        # Arrange
        event_id = "event-123"
        timestamp = datetime.now(timezone.utc)
        aggregate_id = "task-456"
        
        # Act
        event = TaskCreated(
            event_id=event_id,
            timestamp=timestamp,
            aggregate_id=aggregate_id,
            task_title="Test Task",
            user_id="user-789"
        )
        
        # Assert
        assert event.event_id == event_id
        assert event.timestamp == timestamp
        assert event.aggregate_id == aggregate_id
    
    def test_domain_event_auto_generates_event_id_when_empty(self):
        """Test that domain event auto-generates event_id when empty"""
        # Arrange
        timestamp = datetime.now(timezone.utc)
        aggregate_id = "task-456"
        
        # Act
        event = TaskCreated(
            event_id="",
            timestamp=timestamp,
            aggregate_id=aggregate_id,
            task_title="Test Task",
            user_id="user-789"
        )
        
        # Assert
        assert event.event_id != ""
        assert len(event.event_id) > 0
        # Should be a valid UUID format
        import uuid
        uuid.UUID(event.event_id)
    
    def test_domain_event_auto_generates_timestamp_when_none(self):
        """Test that domain event auto-generates timestamp when None"""
        # Arrange
        event_id = "event-123"
        aggregate_id = "task-456"
        
        # Act
        with patch('src.domain.events.base_event.datetime') as mock_datetime:
            mock_now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = mock_now
            event = TaskCreated(
                event_id=event_id,
                timestamp=None,
                aggregate_id=aggregate_id,
                task_title="Test Task",
                user_id="user-789"
            )
        
        # Assert
        assert event.timestamp == mock_now
    
    def test_domain_event_to_dict_includes_base_fields(self):
        """Test that to_dict includes all base domain event fields"""
        # Arrange
        event_id = "event-123"
        timestamp = datetime.now(timezone.utc)
        aggregate_id = "task-456"
        
        # Act
        event = TaskCreated(
            event_id=event_id,
            timestamp=timestamp,
            aggregate_id=aggregate_id,
            task_title="Test Task",
            user_id="user-789"
        )
        event_dict = event.to_dict()
        
        # Assert
        assert event_dict["event_id"] == event_id
        assert event_dict["timestamp"] == timestamp
        assert event_dict["aggregate_id"] == aggregate_id
        assert event_dict["event_type"] == "TaskCreated"
    
    def test_domain_event_mutability_after_creation(self):
        """Test that domain events can be modified after creation (current behavior)"""
        # Arrange
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        original_event_id = event.event_id
        
        # Act - Should be able to modify fields (current dataclass behavior)
        event.event_id = "new-event-id"
        
        # Assert
        assert event.event_id == "new-event-id"
        assert event.event_id != original_event_id


@pytest.mark.domain
@pytest.mark.unit
class TestTaskCreated:
    """Test TaskCreated event"""
    
    def test_task_created_creation_with_valid_data(self):
        """Test creating TaskCreated event with valid data"""
        # Arrange
        event_id = "event-123"
        timestamp = datetime.now(timezone.utc)
        aggregate_id = "task-456"
        task_title = "Complete project documentation"
        user_id = "user-789"
        
        # Act
        event = TaskCreated(
            event_id=event_id,
            timestamp=timestamp,
            aggregate_id=aggregate_id,
            task_title=task_title,
            user_id=user_id
        )
        
        # Assert
        assert event.event_id == event_id
        assert event.timestamp == timestamp
        assert event.aggregate_id == aggregate_id
        assert event.task_title == task_title
        assert event.user_id == user_id
    
    def test_task_created_to_dict_includes_all_fields(self):
        """Test that TaskCreated to_dict includes all fields"""
        # Arrange
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        # Act
        event_dict = event.to_dict()
        
        # Assert
        assert event_dict["event_id"] == "event-123"
        assert event_dict["event_type"] == "TaskCreated"
        assert event_dict["task_title"] == "Test Task"
        assert event_dict["user_id"] == "user-789"
        assert "timestamp" in event_dict
        assert "aggregate_id" in event_dict
    
    def test_task_created_with_empty_task_title(self):
        """Test TaskCreated event with empty task title"""
        # Arrange & Act
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="",
            user_id="user-789"
        )
        
        # Assert
        assert event.task_title == ""
    
    def test_task_created_with_long_task_title(self):
        """Test TaskCreated event with long task title"""
        # Arrange
        long_title = "a" * 500  # Very long title
        
        # Act
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title=long_title,
            user_id="user-789"
        )
        
        # Assert
        assert event.task_title == long_title
        assert len(event.task_title) == 500


@pytest.mark.domain
@pytest.mark.unit
class TestTaskCompleted:
    """Test TaskCompleted event"""
    
    def test_task_completed_creation_with_valid_data(self):
        """Test creating TaskCompleted event with valid data"""
        # Arrange
        event_id = "event-123"
        timestamp = datetime.now(timezone.utc)
        aggregate_id = "task-456"
        task_title = "Complete project documentation"
        user_id = "user-789"
        
        # Act
        event = TaskCompleted(
            event_id=event_id,
            timestamp=timestamp,
            aggregate_id=aggregate_id,
            task_title=task_title,
            user_id=user_id
        )
        
        # Assert
        assert event.event_id == event_id
        assert event.timestamp == timestamp
        assert event.aggregate_id == aggregate_id
        assert event.task_title == task_title
        assert event.user_id == user_id
    
    def test_task_completed_to_dict_includes_all_fields(self):
        """Test that TaskCompleted to_dict includes all fields"""
        # Arrange
        event = TaskCompleted(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        # Act
        event_dict = event.to_dict()
        
        # Assert
        assert event_dict["event_id"] == "event-123"
        assert event_dict["event_type"] == "TaskCompleted"
        assert event_dict["task_title"] == "Test Task"
        assert event_dict["user_id"] == "user-789"
        assert "timestamp" in event_dict
        assert "aggregate_id" in event_dict
    
    def test_task_completed_equality(self):
        """Test TaskCompleted event equality"""
        # Arrange
        timestamp = datetime.now(timezone.utc)
        event1 = TaskCompleted(
            event_id="event-123",
            timestamp=timestamp,
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        event2 = TaskCompleted(
            event_id="event-123",
            timestamp=timestamp,
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        event3 = TaskCompleted(
            event_id="event-456",
            timestamp=timestamp,
            aggregate_id="task-456",
            task_title="Test Task",
            user_id="user-789"
        )
        
        # Assert
        assert event1 == event2  # Same data
        assert event1 != event3  # Different event_id


@pytest.mark.domain
@pytest.mark.unit
class TestTaskStatusChanged:
    """Test TaskStatusChanged event"""
    
    def test_task_status_changed_creation_with_valid_data(self):
        """Test creating TaskStatusChanged event with valid data"""
        # Arrange
        event_id = "event-123"
        timestamp = datetime.now(timezone.utc)
        aggregate_id = "task-456"
        old_status = "pending"
        new_status = "in_progress"
        user_id = "user-789"
        
        # Act
        event = TaskStatusChanged(
            event_id=event_id,
            timestamp=timestamp,
            aggregate_id=aggregate_id,
            old_status=old_status,
            new_status=new_status,
            user_id=user_id
        )
        
        # Assert
        assert event.event_id == event_id
        assert event.timestamp == timestamp
        assert event.aggregate_id == aggregate_id
        assert event.old_status == old_status
        assert event.new_status == new_status
        assert event.user_id == user_id
    
    def test_task_status_changed_to_dict_includes_all_fields(self):
        """Test that TaskStatusChanged to_dict includes all fields"""
        # Arrange
        event = TaskStatusChanged(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            old_status="pending",
            new_status="completed",
            user_id="user-789"
        )
        
        # Act
        event_dict = event.to_dict()
        
        # Assert
        assert event_dict["event_id"] == "event-123"
        assert event_dict["event_type"] == "TaskStatusChanged"
        assert event_dict["old_status"] == "pending"
        assert event_dict["new_status"] == "completed"
        assert event_dict["user_id"] == "user-789"
        assert "timestamp" in event_dict
        assert "aggregate_id" in event_dict
    
    def test_task_status_changed_with_same_status(self):
        """Test TaskStatusChanged event with same old and new status"""
        # Arrange & Act
        event = TaskStatusChanged(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            old_status="pending",
            new_status="pending",  # Same as old
            user_id="user-789"
        )
        
        # Assert
        assert event.old_status == event.new_status
        assert event.old_status == "pending"
    
    def test_task_status_changed_with_all_status_transitions(self):
        """Test TaskStatusChanged event with various status transitions"""
        # Test all possible status transitions
        status_transitions = [
            ("pending", "in_progress"),
            ("in_progress", "completed"),
            ("pending", "completed"),
            ("in_progress", "cancelled"),
            ("pending", "cancelled"),
        ]
        
        for old_status, new_status in status_transitions:
            # Arrange & Act
            event = TaskStatusChanged(
                event_id="event-123",
                timestamp=datetime.now(timezone.utc),
                aggregate_id="task-456",
                old_status=old_status,
                new_status=new_status,
                user_id="user-789"
            )
            
            # Assert
            assert event.old_status == old_status
            assert event.new_status == new_status


@pytest.mark.domain
@pytest.mark.unit
class TestEventSerialization:
    """Test event serialization and deserialization patterns"""
    
    def test_all_events_can_be_serialized_to_dict(self):
        """Test that all event types can be serialized to dictionary"""
        # Arrange
        timestamp = datetime.now(timezone.utc)
        events = [
            TaskCreated(
                event_id="event-1",
                timestamp=timestamp,
                aggregate_id="task-1",
                task_title="Task 1",
                user_id="user-1"
            ),
            TaskCompleted(
                event_id="event-2",
                timestamp=timestamp,
                aggregate_id="task-2",
                task_title="Task 2",
                user_id="user-2"
            ),
            TaskStatusChanged(
                event_id="event-3",
                timestamp=timestamp,
                aggregate_id="task-3",
                old_status="pending",
                new_status="completed",
                user_id="user-3"
            )
        ]
        
        # Act & Assert
        for event in events:
            event_dict = event.to_dict()
            
            # Verify required base fields
            assert "event_id" in event_dict
            assert "timestamp" in event_dict
            assert "aggregate_id" in event_dict
            assert "event_type" in event_dict
            
            # Verify event-specific fields
            if isinstance(event, TaskCreated):
                assert "task_title" in event_dict
                assert "user_id" in event_dict
            elif isinstance(event, TaskCompleted):
                assert "task_title" in event_dict
                assert "user_id" in event_dict
            elif isinstance(event, TaskStatusChanged):
                assert "old_status" in event_dict
                assert "new_status" in event_dict
                assert "user_id" in event_dict
    
    def test_event_type_identification(self):
        """Test that event types can be identified from serialized data"""
        # Arrange
        timestamp = datetime.now(timezone.utc)
        events = [
            TaskCreated(
                event_id="event-1",
                timestamp=timestamp,
                aggregate_id="task-1",
                task_title="Task 1",
                user_id="user-1"
            ),
            TaskCompleted(
                event_id="event-2",
                timestamp=timestamp,
                aggregate_id="task-2",
                task_title="Task 2",
                user_id="user-2"
            ),
            TaskStatusChanged(
                event_id="event-3",
                timestamp=timestamp,
                aggregate_id="task-3",
                old_status="pending",
                new_status="completed",
                user_id="user-3"
            )
        ]
        
        # Act & Assert
        expected_types = ["TaskCreated", "TaskCompleted", "TaskStatusChanged"]
        
        for event, expected_type in zip(events, expected_types):
            event_dict = event.to_dict()
            assert event_dict["event_type"] == expected_type


@pytest.mark.domain
@pytest.mark.unit
class TestEventEdgeCases:
    """Test event edge cases and boundary conditions"""
    
    def test_event_with_empty_aggregate_id(self):
        """Test event creation with empty aggregate_id"""
        # Arrange & Act
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="",
            task_title="Test Task",
            user_id="user-789"
        )
        
        # Assert
        assert event.aggregate_id == ""
    
    def test_event_with_empty_user_id(self):
        """Test event creation with empty user_id"""
        # Arrange & Act
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title="Test Task",
            user_id=""
        )
        
        # Assert
        assert event.user_id == ""
    
    def test_event_with_none_values(self):
        """Test event creation with None values for optional fields"""
        # Arrange & Act
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title=None,
            user_id="user-789"
        )
        
        # Assert
        assert event.task_title is None
    
    def test_event_with_special_characters(self):
        """Test event creation with special characters in fields"""
        # Arrange
        special_title = "Task with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        special_user_id = "user-123!@#$%"
        
        # Act
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title=special_title,
            user_id=special_user_id
        )
        
        # Assert
        assert event.task_title == special_title
        assert event.user_id == special_user_id
        
        # Test serialization
        event_dict = event.to_dict()
        assert event_dict["task_title"] == special_title
        assert event_dict["user_id"] == special_user_id
    
    def test_event_with_unicode_characters(self):
        """Test event creation with unicode characters"""
        # Arrange
        unicode_title = "Tâsk with unicode: ñáéíóú üöäëï"
        unicode_user_id = "user-ñáéíóú"
        
        # Act
        event = TaskCreated(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            aggregate_id="task-456",
            task_title=unicode_title,
            user_id=unicode_user_id
        )
        
        # Assert
        assert event.task_title == unicode_title
        assert event.user_id == unicode_user_id
        
        # Test serialization
        event_dict = event.to_dict()
        assert event_dict["task_title"] == unicode_title
        assert event_dict["user_id"] == unicode_user_id 