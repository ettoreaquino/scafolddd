import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from src.domain.repositories.task_repository import TaskRepository
from src.domain.entities.task import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus


class MockTaskRepository(TaskRepository):
    """Mock implementation of TaskRepository for testing"""
    
    def __init__(self):
        self.tasks = {}
        self.save_called = False
        self.find_by_id_called = False
        self.find_by_user_id_called = False
        self.delete_called = False
        self.exists_called = False
    
    async def save(self, task: Task) -> None:
        """Save a task to the repository"""
        self.save_called = True
        self.tasks[str(task.id)] = task
    
    async def find_by_id(self, task_id: TaskId) -> Task | None:
        """Find a task by its id"""
        self.find_by_id_called = True
        return self.tasks.get(str(task_id))
    
    async def find_by_user_id(self, user_id: UserId) -> list[Task]:
        """Find all tasks for a specific user"""
        self.find_by_user_id_called = True
        return [task for task in self.tasks.values() if task.user_id == user_id]
    
    async def delete(self, task_id: TaskId) -> bool:
        """Delete a task by ID. Returns True if deleted, False if not found"""
        self.delete_called = True
        task_key = str(task_id)
        if task_key in self.tasks:
            del self.tasks[task_key]
            return True
        return False
    
    async def exists(self, task_id: TaskId) -> bool:
        """Check if a task exists"""
        self.exists_called = True
        return str(task_id) in self.tasks


@pytest.fixture
def repository():
    """Create a mock repository instance"""
    return MockTaskRepository()

@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    return Task(
        id=TaskId("task-123"),
        user_id=UserId("user-456"),
        title="Test Task",
        description="A test task for repository testing",
        status=TaskStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def sample_task_2():
    """Create a second sample task for testing"""
    return Task(
        id=TaskId("task-789"),
        user_id=UserId("user-456"),
        title="Another Test Task",
        description="Another test task for the same user",
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def sample_task_different_user():
    """Create a task for a different user"""
    return Task(
        id=TaskId("task-999"),
        user_id=UserId("user-999"),
        title="Different User Task",
        description="A task for a different user",
        status=TaskStatus.COMPLETED,
        created_at=datetime.now(timezone.utc)
    )


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositoryInterface:
    """Test TaskRepository interface contract and behavior"""


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositorySave:
    """Test TaskRepository save method"""
    
    @pytest.mark.asyncio
    async def test_save_new_task(self, repository, sample_task):
        """Test saving a new task to the repository"""
        # Arrange
        task_id = sample_task.id
        
        # Act
        await repository.save(sample_task)
        
        # Assert
        assert repository.save_called
        assert str(task_id) in repository.tasks
        assert repository.tasks[str(task_id)] == sample_task
    
    @pytest.mark.asyncio
    async def test_save_overwrites_existing_task(self, repository, sample_task):
        """Test that saving a task with existing ID overwrites the previous task"""
        # Arrange
        task_id = sample_task.id
        original_task = Task(
            id=task_id,
            user_id=UserId("user-original"),
            title="Original Task",
            description="Original description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        repository.tasks[str(task_id)] = original_task
        
        # Act
        await repository.save(sample_task)
        
        # Assert
        assert repository.save_called
        assert repository.tasks[str(task_id)] == sample_task
        assert repository.tasks[str(task_id)] != original_task
    
    @pytest.mark.asyncio
    async def test_save_multiple_tasks(self, repository, sample_task, sample_task_2):
        """Test saving multiple tasks to the repository"""
        # Arrange
        task_id_1 = sample_task.id
        task_id_2 = sample_task_2.id
        
        # Act
        await repository.save(sample_task)
        await repository.save(sample_task_2)
        
        # Assert
        assert repository.save_called
        assert str(task_id_1) in repository.tasks
        assert str(task_id_2) in repository.tasks
        assert repository.tasks[str(task_id_1)] == sample_task
        assert repository.tasks[str(task_id_2)] == sample_task_2
        assert len(repository.tasks) == 2


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositoryFindById:
    """Test TaskRepository find_by_id method"""
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_task_when_exists(self, repository, sample_task):
        """Test finding a task that exists in the repository"""
        # Arrange
        task_id = sample_task.id
        repository.tasks[str(task_id)] = sample_task
        
        # Act
        result = await repository.find_by_id(task_id)
        
        # Assert
        assert repository.find_by_id_called
        assert result == sample_task
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_task_not_exists(self, repository):
        """Test finding a task that doesn't exist in the repository"""
        # Arrange
        non_existent_task_id = TaskId("non-existent-task")
        
        # Act
        result = await repository.find_by_id(non_existent_task_id)
        
        # Assert
        assert repository.find_by_id_called
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_by_id_with_empty_repository(self, repository):
        """Test finding a task in an empty repository"""
        # Arrange
        task_id = TaskId("any-task-id")
        
        # Act
        result = await repository.find_by_id(task_id)
        
        # Assert
        assert repository.find_by_id_called
        assert result is None


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositoryFindByUserId:
    """Test TaskRepository find_by_user_id method"""
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_user_tasks(self, repository, sample_task, sample_task_2, sample_task_different_user):
        """Test finding all tasks for a specific user"""
        # Arrange
        user_id = UserId("user-456")
        repository.tasks[str(sample_task.id)] = sample_task
        repository.tasks[str(sample_task_2.id)] = sample_task_2
        repository.tasks[str(sample_task_different_user.id)] = sample_task_different_user
        
        # Act
        result = await repository.find_by_user_id(user_id)
        
        # Assert
        assert repository.find_by_user_id_called
        assert len(result) == 2
        assert sample_task in result
        assert sample_task_2 in result
        assert sample_task_different_user not in result
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_empty_list_when_user_has_no_tasks(self, repository, sample_task):
        """Test finding tasks for a user who has no tasks"""
        # Arrange
        user_id = UserId("user-with-no-tasks")
        repository.tasks[str(sample_task.id)] = sample_task
        
        # Act
        result = await repository.find_by_user_id(user_id)
        
        # Assert
        assert repository.find_by_user_id_called
        assert result == []
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_with_empty_repository(self, repository):
        """Test finding tasks for any user in an empty repository"""
        # Arrange
        user_id = UserId("any-user-id")
        
        # Act
        result = await repository.find_by_user_id(user_id)
        
        # Assert
        assert repository.find_by_user_id_called
        assert result == []
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_all_tasks_for_user(self, repository, sample_task, sample_task_2):
        """Test that all tasks for a user are returned regardless of status"""
        # Arrange
        user_id = UserId("user-456")
        repository.tasks[str(sample_task.id)] = sample_task
        repository.tasks[str(sample_task_2.id)] = sample_task_2
        
        # Act
        result = await repository.find_by_user_id(user_id)
        
        # Assert
        assert repository.find_by_user_id_called
        assert len(result) == 2
        # Verify both tasks are returned regardless of their status
        task_ids = [task.id for task in result]
        assert sample_task.id in task_ids
        assert sample_task_2.id in task_ids


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositoryDelete:
    """Test TaskRepository delete method"""
    
    @pytest.mark.asyncio
    async def test_delete_existing_task_returns_true(self, repository, sample_task):
        """Test deleting a task that exists in the repository"""
        # Arrange
        task_id = sample_task.id
        repository.tasks[str(task_id)] = sample_task
        
        # Act
        result = await repository.delete(task_id)
        
        # Assert
        assert repository.delete_called
        assert result is True
        assert str(task_id) not in repository.tasks
    
    @pytest.mark.asyncio
    async def test_delete_non_existing_task_returns_false(self, repository):
        """Test deleting a task that doesn't exist in the repository"""
        # Arrange
        non_existent_task_id = TaskId("non-existent-task")
        
        # Act
        result = await repository.delete(non_existent_task_id)
        
        # Assert
        assert repository.delete_called
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_removes_only_specified_task(self, repository, sample_task, sample_task_2):
        """Test that deleting one task doesn't affect other tasks"""
        # Arrange
        task_id_1 = sample_task.id
        task_id_2 = sample_task_2.id
        repository.tasks[str(task_id_1)] = sample_task
        repository.tasks[str(task_id_2)] = sample_task_2
        
        # Act
        result = await repository.delete(task_id_1)
        
        # Assert
        assert repository.delete_called
        assert result is True
        assert str(task_id_1) not in repository.tasks
        assert str(task_id_2) in repository.tasks
        assert repository.tasks[str(task_id_2)] == sample_task_2
    
    @pytest.mark.asyncio
    async def test_delete_with_empty_repository_returns_false(self, repository):
        """Test deleting a task from an empty repository"""
        # Arrange
        task_id = TaskId("any-task-id")
        
        # Act
        result = await repository.delete(task_id)
        
        # Assert
        assert repository.delete_called
        assert result is False


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositoryExists:
    """Test TaskRepository exists method"""
    
    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing_task(self, repository, sample_task):
        """Test checking existence of a task that exists in the repository"""
        # Arrange
        task_id = sample_task.id
        repository.tasks[str(task_id)] = sample_task
        
        # Act
        result = await repository.exists(task_id)
        
        # Assert
        assert repository.exists_called
        assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_returns_false_for_non_existing_task(self, repository):
        """Test checking existence of a task that doesn't exist in the repository"""
        # Arrange
        non_existent_task_id = TaskId("non-existent-task")
        
        # Act
        result = await repository.exists(non_existent_task_id)
        
        # Assert
        assert repository.exists_called
        assert result is False
    
    @pytest.mark.asyncio
    async def test_exists_with_empty_repository_returns_false(self, repository):
        """Test checking existence of any task in an empty repository"""
        # Arrange
        task_id = TaskId("any-task-id")
        
        # Act
        result = await repository.exists(task_id)
        
        # Assert
        assert repository.exists_called
        assert result is False
    
    @pytest.mark.asyncio
    async def test_exists_after_delete_returns_false(self, repository, sample_task):
        """Test that exists returns false after a task is deleted"""
        # Arrange
        task_id = sample_task.id
        repository.tasks[str(task_id)] = sample_task
        
        # Act
        await repository.delete(task_id)
        result = await repository.exists(task_id)
        
        # Assert
        assert repository.exists_called
        assert result is False


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositoryIntegration:
    """Test TaskRepository methods working together"""
    
    @pytest.mark.asyncio
    async def test_save_then_find_by_id(self, repository, sample_task):
        """Test saving a task and then finding it by ID"""
        # Arrange
        task_id = sample_task.id
        
        # Act
        await repository.save(sample_task)
        found_task = await repository.find_by_id(task_id)
        
        # Assert
        assert found_task == sample_task
        assert found_task.id == task_id
        assert found_task.user_id == sample_task.user_id
        assert found_task.title == sample_task.title
    
    @pytest.mark.asyncio
    async def test_save_then_exists(self, repository, sample_task):
        """Test saving a task and then checking if it exists"""
        # Arrange
        task_id = sample_task.id
        
        # Act
        await repository.save(sample_task)
        exists = await repository.exists(task_id)
        
        # Assert
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_save_then_delete_then_exists(self, repository, sample_task):
        """Test the complete lifecycle: save, delete, then check existence"""
        # Arrange
        task_id = sample_task.id
        
        # Act
        await repository.save(sample_task)
        delete_result = await repository.delete(task_id)
        exists = await repository.exists(task_id)
        
        # Assert
        assert delete_result is True
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_save_multiple_tasks_then_find_by_user_id(self, repository, sample_task, sample_task_2, sample_task_different_user):
        """Test saving multiple tasks and finding them by user ID"""
        # Arrange
        user_id = UserId("user-456")
        
        # Act
        await repository.save(sample_task)
        await repository.save(sample_task_2)
        await repository.save(sample_task_different_user)
        
        user_tasks = await repository.find_by_user_id(user_id)
        
        # Assert
        assert len(user_tasks) == 2
        user_task_ids = [task.id for task in user_tasks]
        assert sample_task.id in user_task_ids
        assert sample_task_2.id in user_task_ids
        assert sample_task_different_user.id not in user_task_ids
    
    @pytest.mark.asyncio
    async def test_repository_state_consistency(self, repository, sample_task, sample_task_2):
        """Test that repository maintains consistent state across operations"""
        # Arrange
        task_id_1 = sample_task.id
        task_id_2 = sample_task_2.id
        
        # Act & Assert
        # Initially empty
        assert await repository.exists(task_id_1) is False
        assert await repository.exists(task_id_2) is False
        
        # Save first task
        await repository.save(sample_task)
        assert await repository.exists(task_id_1) is True
        assert await repository.exists(task_id_2) is False
        
        # Save second task
        await repository.save(sample_task_2)
        assert await repository.exists(task_id_1) is True
        assert await repository.exists(task_id_2) is True
        
        # Delete first task
        await repository.delete(task_id_1)
        assert await repository.exists(task_id_1) is False
        assert await repository.exists(task_id_2) is True
        
        # Delete second task
        await repository.delete(task_id_2)
        assert await repository.exists(task_id_1) is False
        assert await repository.exists(task_id_2) is False


@pytest.mark.domain
@pytest.mark.unit
class TestTaskRepositoryEdgeCases:
    """Test TaskRepository edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_save_task_with_same_id_multiple_times(self, repository, sample_task):
        """Test saving the same task multiple times"""
        # Arrange
        task_id = sample_task.id
        
        # Act
        await repository.save(sample_task)
        await repository.save(sample_task)
        await repository.save(sample_task)
        
        # Assert
        assert len(repository.tasks) == 1
        assert repository.tasks[str(task_id)] == sample_task
    
    @pytest.mark.asyncio
    async def test_find_by_id_with_different_task_id_objects(self, repository, sample_task):
        """Test that find_by_id works with different TaskId objects with same value"""
        # Arrange
        task_id_1 = TaskId("task-123")
        task_id_2 = TaskId("task-123")  # Same value, different object
        sample_task.id = task_id_1
        repository.tasks[str(task_id_1)] = sample_task
        
        # Act
        result = await repository.find_by_id(task_id_2)
        
        # Assert
        assert result == sample_task
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_with_different_user_id_objects(self, repository, sample_task):
        """Test that find_by_user_id works with different UserId objects with same value"""
        # Arrange
        user_id_1 = UserId("user-456")
        user_id_2 = UserId("user-456")  # Same value, different object
        sample_task.user_id = user_id_1
        repository.tasks[str(sample_task.id)] = sample_task
        
        # Act
        result = await repository.find_by_user_id(user_id_2)
        
        # Assert
        assert len(result) == 1
        assert result[0] == sample_task
    
    @pytest.mark.asyncio
    async def test_delete_task_then_save_same_id(self, repository, sample_task):
        """Test deleting a task and then saving a new task with the same ID"""
        # Arrange
        task_id = sample_task.id
        repository.tasks[str(task_id)] = sample_task
        
        # Act
        await repository.delete(task_id)
        await repository.save(sample_task)
        
        # Assert
        assert await repository.exists(task_id) is True
        found_task = await repository.find_by_id(task_id)
        assert found_task == sample_task 