import pytest
import uuid
from src.domain.value_objects import TaskId, UserId, TaskStatus

@pytest.mark.domain
@pytest.mark.unit
class TestTaskId:
    """Test TaskId value object (existing implementation)"""
    
    def test_task_id_creation_with_valid_value(self):
        """Test creating TaskId with valid string value"""
        task_id = TaskId("task-123")
        assert str(task_id) == "task-123"
        assert task_id.value == "task-123"
    
    def test_task_id_creation_with_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="TaskId cannot be empty"):
            TaskId("")
    
    def test_task_id_creation_with_none_raises_error(self):
        """Test that None value raises ValueError"""
        with pytest.raises(ValueError, match="TaskId cannot be empty"):
            TaskId(None)
    
    def test_task_id_creation_with_non_string_raises_error(self):
        """Test that non-string value raises ValueError"""
        with pytest.raises(ValueError, match="TaskId cannot be empty"):
            TaskId(123)
    
    def test_task_id_generation_creates_unique_id(self):
        """Test that generate() creates unique IDs with task- prefix"""
        task_id1 = TaskId.generate()
        task_id2 = TaskId.generate()
        
        assert task_id1 != task_id2
        assert task_id1.value.startswith("task-")
        assert task_id2.value.startswith("task-")
        
        # Verify it's a valid UUID format after the prefix
        uuid_part1 = task_id1.value.replace("task-", "")
        uuid_part2 = task_id2.value.replace("task-", "")
        
        # Should be valid UUIDs
        uuid.UUID(uuid_part1)
        uuid.UUID(uuid_part2)
    
    def test_task_id_equality(self):
        """Test TaskId equality comparison"""
        task_id1 = TaskId("task-123")
        task_id2 = TaskId("task-123")
        task_id3 = TaskId("task-456")
        
        assert task_id1 == task_id2
        assert task_id1 != task_id3

@pytest.mark.domain
@pytest.mark.unit
class TestUserId:
    """Test UserId value object (existing implementation)"""
    
    def test_user_id_creation_with_valid_value(self):
        """Test creating UserId with valid string value"""
        user_id = UserId("user-123")
        assert str(user_id) == "user-123"
        assert user_id.value == "user-123"
    
    def test_user_id_creation_with_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="UserId must be an non-empty string"):
            UserId("")
    
    def test_user_id_creation_with_none_raises_error(self):
        """Test that None value raises ValueError"""
        with pytest.raises(ValueError, match="UserId must be an non-empty string"):
            UserId(None)
    
    def test_user_id_creation_with_non_string_raises_error(self):
        """Test that non-string value raises ValueError"""
        with pytest.raises(ValueError, match="UserId must be an non-empty string"):
            UserId(123)
    
    def test_user_id_equality(self):
        """Test UserId equality comparison"""
        user_id1 = UserId("user-123")
        user_id2 = UserId("user-123")
        user_id3 = UserId("user-456")
        
        assert user_id1 == user_id2
        assert user_id1 != user_id3

@pytest.mark.domain
@pytest.mark.unit
class TestTaskStatus:
    """Test TaskStatus value object (existing implementation)"""
    
    def test_task_status_enum_values(self):
        """Test that all expected status values exist"""
        assert TaskStatus.PENDING == TaskStatus("pending")
        assert TaskStatus.IN_PROGRESS == TaskStatus("in_progress")
        assert TaskStatus.COMPLETED == TaskStatus("completed")
        assert TaskStatus.CANCELLED == TaskStatus("cancelled")
    
    def test_task_status_string_representation(self):
        """Test string representation of task status"""
        assert str(TaskStatus.PENDING) == "pending"
        assert str(TaskStatus.IN_PROGRESS) == "in_progress"
        assert str(TaskStatus.COMPLETED) == "completed"
        assert str(TaskStatus.CANCELLED) == "cancelled"
    
    def test_task_status_comparison(self):
        """Test TaskStatus comparison"""
        assert TaskStatus.PENDING == TaskStatus.PENDING
        assert TaskStatus.PENDING != TaskStatus.COMPLETED
    
    def test_task_status_enum_membership(self):
        """Test that TaskStatus values are proper enum members"""
        assert TaskStatus.PENDING in TaskStatus
        assert TaskStatus.IN_PROGRESS in TaskStatus
        assert TaskStatus.COMPLETED in TaskStatus
        assert TaskStatus.CANCELLED in TaskStatus 