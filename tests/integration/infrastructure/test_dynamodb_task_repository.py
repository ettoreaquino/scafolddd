# tests/integration/infrastructure/test_dynamodb_task_repository.py
import pytest
import boto3

from datetime import datetime, timezone
from moto import mock_aws

from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus
from src.infrastructure.repositories.dynamodb_task_repository import DynamoDBTaskRepository


# Test fixtures for integration tests
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


def create_dynamodb_table():
    """Helper function to create DynamoDB table for integration tests"""
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