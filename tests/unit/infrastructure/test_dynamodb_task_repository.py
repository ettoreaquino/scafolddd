# tests/unit/infrastructure/test_dynamodb_task_repository.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from moto import mock_aws
import boto3
from botocore.exceptions import ClientError

from src.infrastructure.repositories.dynamodb_task_repository import DynamoDBTaskRepository
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus


# Test fixtures and helpers
@pytest.fixture
def task_id():
    """Test task ID fixture"""
    return TaskId("task-123e4567-e89b-12d3-a456-426614174000")


@pytest.fixture
def user_id():
    """Test user ID fixture"""
    return UserId("user-456")


@pytest.fixture
def test_task(task_id, user_id):
    """Create a test task fixture"""
    return Task(
        id=task_id,
        user_id=user_id,
        title="Test Task",
        description="This is a test task",
        status=TaskStatus.PENDING,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
        completed_at=None
    )


@pytest.fixture
def completed_task(task_id, user_id):
    """Create a completed test task fixture"""
    return Task(
        id=task_id,
        user_id=user_id,
        title="Completed Task",
        description="This is a completed task",
        status=TaskStatus.COMPLETED,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
    )


@pytest.fixture
def mock_table():
    """Mock DynamoDB table fixture"""
    table = Mock()
    table.put_item = Mock()
    table.get_item = Mock()
    table.query = Mock()
    table.delete_item = Mock()
    return table


@pytest.fixture
def repository_with_mock(mock_table):
    """Repository with mocked table"""
    repository = DynamoDBTaskRepository("test-table")
    repository._table = mock_table
    repository._dynamodb = Mock()
    return repository


def create_dynamodb_table():
    """Helper function to create DynamoDB table"""
    # Create mock DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create table
    table = dynamodb.create_table(
        TableName='test-tasks',
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Wait for table to be created
    table.meta.client.get_waiter('table_exists').wait(TableName='test-tasks')
    
    return table


@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBTaskRepository:
    """Unit tests for DynamoDB Task Repository"""
    
    def test_repository_implements_interface(self):
        """Test that repository implements TaskRepository interface"""
        repository = DynamoDBTaskRepository("test-table")
        
        # Verify all required methods exist
        assert hasattr(repository, 'save')
        assert hasattr(repository, 'find_by_id')
        assert hasattr(repository, 'find_by_user_id')
        assert hasattr(repository, 'delete')
        assert hasattr(repository, 'exists')
        
        # Verify methods are callable
        assert callable(repository.save)
        assert callable(repository.find_by_id)
        assert callable(repository.find_by_user_id)
        assert callable(repository.delete)
        assert callable(repository.exists)
    
    def test_repository_initialization(self):
        """Test repository is initialized correctly"""
        table_name = "test-table"
        repository = DynamoDBTaskRepository(table_name)
        
        assert repository.table_name == table_name
        assert repository._dynamodb is None
        assert repository._table is None
    
    @pytest.mark.asyncio
    async def test_save_task_creates_correct_item(self, repository_with_mock, test_task):
        """Test that save method creates correct DynamoDB item structure"""
        await repository_with_mock.save(test_task)
        
        # Verify put_item was called
        repository_with_mock._table.put_item.assert_called_once()
        
        # Get the item that was saved
        call_args = repository_with_mock._table.put_item.call_args
        item = call_args[1]['Item']
        
        # Verify item structure
        assert item['PK'] == f'TASK#{test_task.id}'
        assert item['SK'] == f'TASK#{test_task.id}'
        assert item['GSI1PK'] == f'USER#{test_task.user_id}'
        assert item['GSI1SK'] == f'TASK#{test_task.created_at.isoformat()}#{test_task.id}'
        assert item['Type'] == 'Task'
        assert item['TaskId'] == str(test_task.id)
        assert item['UserId'] == str(test_task.user_id)
        assert item['Title'] == test_task.title
        assert item['Description'] == test_task.description
        assert item['Status'] == test_task.status.value
        assert item['CreatedAt'] == test_task.created_at.isoformat()
        
        # UpdatedAt and CompletedAt should not be in item for new task
        assert 'UpdatedAt' not in item
        assert 'CompletedAt' not in item
    
    @pytest.mark.asyncio
    async def test_save_completed_task_includes_timestamps(self, repository_with_mock, completed_task):
        """Test that save method includes all timestamps for completed task"""
        await repository_with_mock.save(completed_task)
        
        call_args = repository_with_mock._table.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['UpdatedAt'] == completed_task.updated_at.isoformat()
        assert item['CompletedAt'] == completed_task.completed_at.isoformat()
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_task_when_found(self, repository_with_mock, test_task):
        """Test find_by_id returns task when it exists"""
        # Mock the response
        mock_response = {
            'Item': {
                'PK': f'TASK#{test_task.id}',
                'SK': f'TASK#{test_task.id}',
                'TaskId': str(test_task.id),
                'UserId': str(test_task.user_id),
                'Title': test_task.title,
                'Description': test_task.description,
                'Status': test_task.status.value,
                'CreatedAt': test_task.created_at.isoformat(),
                'Type': 'Task'
            }
        }
        repository_with_mock._table.get_item.return_value = mock_response
        
        result = await repository_with_mock.find_by_id(test_task.id)
        
        # Verify get_item was called correctly
        repository_with_mock._table.get_item.assert_called_once_with(
            Key={
                'PK': f'TASK#{test_task.id}',
                'SK': f'TASK#{test_task.id}'
            }
        )
        
        # Verify returned task
        assert result is not None
        assert result.id == test_task.id
        assert result.user_id == test_task.user_id
        assert result.title == test_task.title
        assert result.description == test_task.description
        assert result.status == test_task.status
        assert result.created_at == test_task.created_at
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_not_found(self, repository_with_mock, task_id):
        """Test find_by_id returns None when task doesn't exist"""
        # Mock empty response
        repository_with_mock._table.get_item.return_value = {}
        
        result = await repository_with_mock.find_by_id(task_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_user_tasks(self, repository_with_mock, user_id):
        """Test find_by_user_id returns all tasks for a user"""
        # Mock query response with multiple tasks
        mock_response = {
            'Items': [
                {
                    'TaskId': 'task-1',
                    'UserId': str(user_id),
                    'Title': 'Task 1',
                    'Description': 'First task',
                    'Status': 'pending',
                    'CreatedAt': '2024-01-01T12:00:00+00:00',
                    'Type': 'Task'
                },
                {
                    'TaskId': 'task-2',
                    'UserId': str(user_id),
                    'Title': 'Task 2',
                    'Description': 'Second task',
                    'Status': 'completed',
                    'CreatedAt': '2024-01-01T13:00:00+00:00',
                    'Type': 'Task'
                }
            ]
        }
        repository_with_mock._table.query.return_value = mock_response
        
        result = await repository_with_mock.find_by_user_id(user_id)
        
        # Verify query was called correctly
        repository_with_mock._table.query.assert_called_once()
        call_args = repository_with_mock._table.query.call_args
        assert call_args[1]['IndexName'] == 'GSI1'
        assert call_args[1]['ScanIndexForward'] is False
        
        # Verify results
        assert len(result) == 2
        assert all(task.user_id == user_id for task in result)
        assert result[0].title == 'Task 1'
        assert result[1].title == 'Task 2'
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_empty_list_when_no_tasks(self, repository_with_mock, user_id):
        """Test find_by_user_id returns empty list when user has no tasks"""
        repository_with_mock._table.query.return_value = {'Items': []}
        
        result = await repository_with_mock.find_by_user_id(user_id)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_delete_task_removes_item(self, repository_with_mock, task_id):
        """Test delete method removes task from DynamoDB"""
        # Mock successful deletion
        repository_with_mock._table.delete_item.return_value = {
            'Attributes': {'TaskId': str(task_id)}
        }
        
        result = await repository_with_mock.delete(task_id)
        
        # Verify delete_item was called correctly
        repository_with_mock._table.delete_item.assert_called_once_with(
            Key={
                'PK': f'TASK#{task_id}',
                'SK': f'TASK#{task_id}'
            },
            ReturnValues='ALL_OLD'
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_returns_false_when_item_not_found(self, repository_with_mock, task_id):
        """Test delete returns False when task doesn't exist"""
        repository_with_mock._table.delete_item.return_value = {}
        
        result = await repository_with_mock.delete(task_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_exists_returns_true_when_task_exists(self, repository_with_mock, test_task):
        """Test exists returns True when task exists"""
        # Mock find_by_id to return a task
        with patch.object(repository_with_mock, 'find_by_id', return_value=test_task):
            result = await repository_with_mock.exists(test_task.id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_returns_false_when_task_not_found(self, repository_with_mock, task_id):
        """Test exists returns False when task doesn't exist"""
        # Mock find_by_id to return None
        with patch.object(repository_with_mock, 'find_by_id', return_value=None):
            result = await repository_with_mock.exists(task_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_handle_dynamodb_exceptions(self, repository_with_mock, test_task):
        """Test that DynamoDB exceptions are handled gracefully"""
        # Mock DynamoDB error
        repository_with_mock._table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
            'PutItem'
        )
        
        # Should not raise exception, but handle it gracefully
        with pytest.raises(ClientError):
            await repository_with_mock.save(test_task)
    
    def test_map_to_entity_converts_dynamodb_item_correctly(self):
        """Test _map_to_entity converts DynamoDB item to Task entity"""
        repository = DynamoDBTaskRepository("test-table")
        
        item = {
            'TaskId': 'task-123',
            'UserId': 'user-456',
            'Title': 'Test Task',
            'Description': 'Test Description',
            'Status': 'pending',
            'CreatedAt': '2024-01-01T12:00:00+00:00',
            'UpdatedAt': '2024-01-01T13:00:00+00:00',
            'CompletedAt': '2024-01-01T14:00:00+00:00'
        }
        
        task = repository._map_to_entity(item)
        
        assert task.id.value == 'task-123'
        assert task.user_id.value == 'user-456'
        assert task.title == 'Test Task'
        assert task.description == 'Test Description'
        assert task.status == TaskStatus.PENDING
        assert task.created_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert task.updated_at == datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        assert task.completed_at == datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
    
    def test_map_to_entity_handles_optional_fields(self):
        """Test _map_to_entity handles missing optional fields"""
        repository = DynamoDBTaskRepository("test-table")
        
        item = {
            'TaskId': 'task-123',
            'UserId': 'user-456',
            'Title': 'Test Task',
            'Description': 'Test Description',
            'Status': 'pending',
            'CreatedAt': '2024-01-01T12:00:00+00:00'
            # No UpdatedAt or CompletedAt
        }
        
        task = repository._map_to_entity(item)
        
        assert task.updated_at is None
        assert task.completed_at is None


@pytest.mark.infrastructure
@pytest.mark.integration
class TestDynamoDBTaskRepositoryIntegration:
    """Integration tests with real DynamoDB (mocked with moto)"""
    
    @pytest.mark.asyncio
    async def test_full_crud_operations(self, test_task):
        """Test complete CRUD operations with real DynamoDB"""
        with mock_aws():
            # Create the table within the test
            dynamodb_table = create_dynamodb_table()
            repository = DynamoDBTaskRepository("test-tasks")
            
            # Test save
            await repository.save(test_task)
            
            # Test find by ID
            found_task = await repository.find_by_id(test_task.id)
            assert found_task is not None
            assert found_task.id == test_task.id
            assert found_task.title == test_task.title
            
            # Test find by user ID
            user_tasks = await repository.find_by_user_id(test_task.user_id)
            assert len(user_tasks) == 1
            assert user_tasks[0].id == test_task.id
            
            # Test exists
            exists = await repository.exists(test_task.id)
            assert exists is True
            
            # Test delete
            deleted = await repository.delete(test_task.id)
            assert deleted is True
            
            # Verify deletion
            found_after_delete = await repository.find_by_id(test_task.id)
            assert found_after_delete is None
            
            exists_after_delete = await repository.exists(test_task.id)
            assert exists_after_delete is False
    
    @pytest.mark.asyncio
    async def test_find_by_user_id_ordering(self, user_id):
        """Test that find_by_user_id returns tasks in correct order (newest first)"""
        with mock_aws():
            # Create the table within the test
            dynamodb_table = create_dynamodb_table()
            repository = DynamoDBTaskRepository("test-tasks")
            
            # Create tasks with different timestamps
            tasks = []
            for i in range(3):
                task = Task(
                    id=TaskId(f"task-{i}"),
                    user_id=user_id,
                    title=f"Task {i}",
                    description=f"Description {i}",
                    status=TaskStatus.PENDING,
                    created_at=datetime(2024, 1, 1, 12, i, 0, tzinfo=timezone.utc)
                )
                tasks.append(task)
                await repository.save(task)
            
            # Find tasks by user ID
            found_tasks = await repository.find_by_user_id(user_id)
            
            # Verify order (newest first)
            assert len(found_tasks) == 3
            assert found_tasks[0].title == "Task 2"  # Latest timestamp
            assert found_tasks[1].title == "Task 1"
            assert found_tasks[2].title == "Task 0"  # Earliest timestamp 