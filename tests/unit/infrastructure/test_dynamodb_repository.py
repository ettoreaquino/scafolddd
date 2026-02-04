import pytest
import os
import boto3
from datetime import datetime, timezone
from moto import mock_aws
from src.infrastructure.repositories.dynamodb_task_repository import DynamoDBTaskRepository
from src.domain.repositories import TaskRepository
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus


# ============================================================================
# Test Constants
# ============================================================================

TABLE_NAME = "test-tasks"
TASK_ID_1 = "task-001"
TASK_ID_2 = "task-002"
TASK_ID_3 = "task-003"
USER_ID_1 = "user-123"
USER_ID_2 = "user-456"
TASK_TITLE = "Test Task"
TASK_DESCRIPTION = "A test task description"


# ============================================================================
# Helpers
# ============================================================================

def create_dynamodb_table():
    """Create a DynamoDB table with the expected schema"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                },
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5,
        },
    )
    table.wait_until_exists()
    return table


def create_test_task(
    task_id: str = TASK_ID_1,
    user_id: str = USER_ID_1,
    title: str = TASK_TITLE,
    description: str = TASK_DESCRIPTION,
    status: TaskStatus = TaskStatus.PENDING,
    created_at: datetime = None,
    updated_at: datetime = None,
    completed_at: datetime = None,
) -> Task:
    """Create a test task entity"""
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    task = Task(
        id=TaskId(task_id),
        user_id=UserId(user_id),
        title=title,
        description=description,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        completed_at=completed_at,
    )
    # Clear any events generated during construction
    task.pop_events()
    return task


def create_task_with_user(user_id: UserId, title: str) -> Task:
    """Create a test task with a specific user"""
    task = Task(
        id=TaskId.generate(),
        user_id=user_id,
        title=title,
        description=f"Description for {title}",
        status=TaskStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )
    task.pop_events()
    return task


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def aws_credentials():
    """Set mock AWS credentials for moto"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield
    # Cleanup handled by fixture teardown


@pytest.fixture
def mock_dynamodb():
    """Create a mocked DynamoDB environment"""
    with mock_aws():
        create_dynamodb_table()
        yield


@pytest.fixture
def repository(mock_dynamodb):
    """Create a DynamoDBTaskRepository with mocked DynamoDB"""
    return DynamoDBTaskRepository(TABLE_NAME)


# ============================================================================
# Test: Repository Interface Compliance
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBRepositoryInterfaceCompliance:
    """Test that DynamoDBTaskRepository implements the TaskRepository interface"""

    def test_repository_is_subclass_of_task_repository(self):
        """Test that DynamoDBTaskRepository inherits from TaskRepository"""
        assert issubclass(DynamoDBTaskRepository, TaskRepository)

    def test_repository_implements_save(self, repository):
        """Test that repository has a save method"""
        assert hasattr(repository, 'save')
        assert callable(getattr(repository, 'save'))

    def test_repository_implements_find_by_id(self, repository):
        """Test that repository has a find_by_id method"""
        assert hasattr(repository, 'find_by_id')
        assert callable(getattr(repository, 'find_by_id'))

    def test_repository_implements_find_by_user_id(self, repository):
        """Test that repository has a find_by_user_id method"""
        assert hasattr(repository, 'find_by_user_id')
        assert callable(getattr(repository, 'find_by_user_id'))

    def test_repository_implements_delete(self, repository):
        """Test that repository has a delete method"""
        assert hasattr(repository, 'delete')
        assert callable(getattr(repository, 'delete'))

    def test_repository_implements_exists(self, repository):
        """Test that repository has an exists method"""
        assert hasattr(repository, 'exists')
        assert callable(getattr(repository, 'exists'))

    def test_repository_stores_table_name(self, repository):
        """Test that repository stores the table name"""
        assert repository.table_name == TABLE_NAME


# ============================================================================
# Test: DynamoDB Item Mapping
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBItemMapping:
    """Test DynamoDB item mapping (entity <-> DynamoDB item)"""

    @pytest.mark.asyncio
    async def test_save_task_creates_correct_pk(self, repository):
        """Test that saved task has correct primary key"""
        task = create_test_task()
        await repository.save(task)

        table = repository.table
        response = table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )

        item = response['Item']
        assert item['PK'] == f'TASK#{TASK_ID_1}'
        assert item['SK'] == f'TASK#{TASK_ID_1}'

    @pytest.mark.asyncio
    async def test_save_task_creates_correct_gsi_keys(self, repository):
        """Test that saved task has correct GSI1 keys"""
        task = create_test_task()
        await repository.save(task)

        table = repository.table
        response = table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )

        item = response['Item']
        assert item['GSI1PK'] == f'USER#{USER_ID_1}'
        assert item['GSI1SK'].startswith(f'TASK#')
        assert str(TASK_ID_1) in item['GSI1SK']

    @pytest.mark.asyncio
    async def test_save_task_maps_all_attributes(self, repository):
        """Test that all task attributes are saved correctly"""
        task = create_test_task()
        await repository.save(task)

        table = repository.table
        response = table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )

        item = response['Item']
        assert item['Type'] == 'Task'
        assert item['TaskId'] == TASK_ID_1
        assert item['UserId'] == USER_ID_1
        assert item['Title'] == TASK_TITLE
        assert item['Description'] == TASK_DESCRIPTION
        assert item['Status'] == 'pending'
        assert 'CreatedAt' in item

    @pytest.mark.asyncio
    async def test_save_task_excludes_none_values(self, repository):
        """Test that None values are not saved to DynamoDB"""
        task = create_test_task()
        await repository.save(task)

        table = repository.table
        response = table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )

        item = response['Item']
        assert 'UpdatedAt' not in item
        assert 'CompletedAt' not in item

    @pytest.mark.asyncio
    async def test_save_completed_task_includes_all_timestamps(self, repository):
        """Test that completed task includes all timestamp fields"""
        now = datetime.now(timezone.utc)
        task = create_test_task(
            status=TaskStatus.COMPLETED,
            updated_at=now,
            completed_at=now
        )
        await repository.save(task)

        table = repository.table
        response = table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )

        item = response['Item']
        assert 'UpdatedAt' in item
        assert 'CompletedAt' in item

    @pytest.mark.asyncio
    async def test_map_to_entity_reconstructs_task(self, repository):
        """Test that _map_to_entity correctly reconstructs a Task entity"""
        task = create_test_task()
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))

        assert found is not None
        assert str(found.id) == TASK_ID_1
        assert str(found.user_id) == USER_ID_1
        assert found.title == TASK_TITLE
        assert found.description == TASK_DESCRIPTION
        assert found.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_map_to_entity_handles_completed_task(self, repository):
        """Test that _map_to_entity correctly handles completed task timestamps"""
        now = datetime.now(timezone.utc)
        task = create_test_task(
            status=TaskStatus.COMPLETED,
            updated_at=now,
            completed_at=now
        )
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))

        assert found is not None
        assert found.status == TaskStatus.COMPLETED
        assert found.updated_at is not None
        assert found.completed_at is not None


# ============================================================================
# Test: Save Operation
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBSaveOperation:
    """Test saving tasks to DynamoDB"""

    @pytest.mark.asyncio
    async def test_save_task_succeeds(self, repository):
        """Test that saving a task completes without error"""
        task = create_test_task()
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))
        assert found is not None

    @pytest.mark.asyncio
    async def test_save_task_is_idempotent(self, repository):
        """Test that saving the same task twice overwrites cleanly"""
        task = create_test_task()
        await repository.save(task)
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))
        assert found is not None
        assert found.title == TASK_TITLE

    @pytest.mark.asyncio
    async def test_save_updated_task_overwrites(self, repository):
        """Test that saving an updated task overwrites the old one"""
        task = create_test_task()
        await repository.save(task)

        task.update_details(title="Updated Title")
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))
        assert found is not None
        assert found.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_save_multiple_tasks(self, repository):
        """Test saving multiple different tasks"""
        task1 = create_test_task(task_id=TASK_ID_1, title="Task 1")
        task2 = create_test_task(task_id=TASK_ID_2, title="Task 2")
        task3 = create_test_task(task_id=TASK_ID_3, title="Task 3")

        await repository.save(task1)
        await repository.save(task2)
        await repository.save(task3)

        found1 = await repository.find_by_id(TaskId(TASK_ID_1))
        found2 = await repository.find_by_id(TaskId(TASK_ID_2))
        found3 = await repository.find_by_id(TaskId(TASK_ID_3))

        assert found1 is not None and found1.title == "Task 1"
        assert found2 is not None and found2.title == "Task 2"
        assert found3 is not None and found3.title == "Task 3"

    @pytest.mark.asyncio
    async def test_save_task_with_empty_description(self, repository):
        """Test saving a task with an empty description"""
        task = create_test_task(description="")
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))
        assert found is not None
        assert found.description == ""


# ============================================================================
# Test: Find By ID Operation
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBFindById:
    """Test finding tasks by ID"""

    @pytest.mark.asyncio
    async def test_find_by_id_returns_task(self, repository):
        """Test finding a task by its ID"""
        task = create_test_task()
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))

        assert found is not None
        assert str(found.id) == TASK_ID_1
        assert found.title == TASK_TITLE
        assert str(found.user_id) == USER_ID_1
        assert found.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_not_found(self, repository):
        """Test finding a task that doesn't exist returns None"""
        found = await repository.find_by_id(TaskId("non-existent-task"))
        assert found is None

    @pytest.mark.asyncio
    async def test_find_by_id_returns_correct_task_among_many(self, repository):
        """Test finding the correct task when multiple tasks exist"""
        task1 = create_test_task(task_id=TASK_ID_1, title="First Task")
        task2 = create_test_task(task_id=TASK_ID_2, title="Second Task")

        await repository.save(task1)
        await repository.save(task2)

        found = await repository.find_by_id(TaskId(TASK_ID_2))
        assert found is not None
        assert found.title == "Second Task"

    @pytest.mark.asyncio
    async def test_find_by_id_preserves_all_fields(self, repository):
        """Test that find_by_id preserves all task fields"""
        now = datetime.now(timezone.utc)
        task = create_test_task(
            status=TaskStatus.IN_PROGRESS,
            updated_at=now,
        )
        await repository.save(task)

        found = await repository.find_by_id(TaskId(TASK_ID_1))

        assert found is not None
        assert found.description == TASK_DESCRIPTION
        assert found.status == TaskStatus.IN_PROGRESS
        assert found.updated_at is not None


# ============================================================================
# Test: Find By User ID Operation
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBFindByUserId:
    """Test finding tasks by user ID"""

    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_user_tasks(self, repository):
        """Test finding all tasks for a user"""
        user_id = UserId(USER_ID_1)
        for i in range(3):
            task = create_task_with_user(user_id, f"Task {i}")
            await repository.save(task)

        found_tasks = await repository.find_by_user_id(user_id)

        assert len(found_tasks) == 3
        assert all(str(t.user_id) == USER_ID_1 for t in found_tasks)

    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_empty_for_unknown_user(self, repository):
        """Test that unknown user returns empty list"""
        found_tasks = await repository.find_by_user_id(UserId("unknown-user"))
        assert found_tasks == []

    @pytest.mark.asyncio
    async def test_find_by_user_id_only_returns_user_tasks(self, repository):
        """Test that find_by_user_id only returns tasks for the specified user"""
        user1 = UserId(USER_ID_1)
        user2 = UserId(USER_ID_2)

        task1 = create_task_with_user(user1, "User 1 Task")
        task2 = create_task_with_user(user2, "User 2 Task")

        await repository.save(task1)
        await repository.save(task2)

        found_tasks = await repository.find_by_user_id(user1)

        assert len(found_tasks) == 1
        assert str(found_tasks[0].user_id) == USER_ID_1
        assert found_tasks[0].title == "User 1 Task"

    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_tasks_with_different_statuses(self, repository):
        """Test finding user tasks with different statuses"""
        user_id = UserId(USER_ID_1)

        task_pending = create_test_task(task_id=TASK_ID_1, user_id=USER_ID_1, title="Pending", status=TaskStatus.PENDING)
        task_completed = create_test_task(task_id=TASK_ID_2, user_id=USER_ID_1, title="Completed", status=TaskStatus.COMPLETED, completed_at=datetime.now(timezone.utc))

        await repository.save(task_pending)
        await repository.save(task_completed)

        found_tasks = await repository.find_by_user_id(user_id)

        assert len(found_tasks) == 2
        statuses = {t.status for t in found_tasks}
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.COMPLETED in statuses


# ============================================================================
# Test: Delete Operation
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBDeleteOperation:
    """Test deleting tasks from DynamoDB"""

    @pytest.mark.asyncio
    async def test_delete_removes_task(self, repository):
        """Test that delete removes the task from DynamoDB"""
        task = create_test_task()
        await repository.save(task)

        # Verify task exists
        found = await repository.find_by_id(TaskId(TASK_ID_1))
        assert found is not None

        # Delete task
        result = await repository.delete(TaskId(TASK_ID_1))

        # Verify task is deleted
        found = await repository.find_by_id(TaskId(TASK_ID_1))
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_task_exists(self, repository):
        """Test that delete returns True when task was deleted"""
        task = create_test_task()
        await repository.save(task)

        result = await repository.delete(TaskId(TASK_ID_1))
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_task_not_found(self, repository):
        """Test that delete returns False when task doesn't exist"""
        result = await repository.delete(TaskId("non-existent"))
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_only_removes_target_task(self, repository):
        """Test that deleting one task doesn't affect others"""
        task1 = create_test_task(task_id=TASK_ID_1, title="Task 1")
        task2 = create_test_task(task_id=TASK_ID_2, title="Task 2")

        await repository.save(task1)
        await repository.save(task2)

        await repository.delete(TaskId(TASK_ID_1))

        found1 = await repository.find_by_id(TaskId(TASK_ID_1))
        found2 = await repository.find_by_id(TaskId(TASK_ID_2))

        assert found1 is None
        assert found2 is not None
        assert found2.title == "Task 2"


# ============================================================================
# Test: Exists Operation
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestDynamoDBExistsOperation:
    """Test checking if tasks exist"""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing_task(self, repository):
        """Test that exists returns True for existing task"""
        task = create_test_task()
        await repository.save(task)

        result = await repository.exists(TaskId(TASK_ID_1))
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_nonexistent_task(self, repository):
        """Test that exists returns False for nonexistent task"""
        result = await repository.exists(TaskId("non-existent"))
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_false_after_delete(self, repository):
        """Test that exists returns False after task is deleted"""
        task = create_test_task()
        await repository.save(task)

        await repository.delete(TaskId(TASK_ID_1))

        result = await repository.exists(TaskId(TASK_ID_1))
        assert result is False


# ============================================================================
# Test: Single-Table Design
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestSingleTableDesign:
    """Test DynamoDB single-table design implementation"""

    @pytest.mark.asyncio
    async def test_pk_format_is_task_prefix(self, repository):
        """Test that PK follows TASK#{id} format"""
        task = create_test_task()
        await repository.save(task)

        response = repository.table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )
        assert 'Item' in response
        assert response['Item']['PK'] == f'TASK#{TASK_ID_1}'

    @pytest.mark.asyncio
    async def test_sk_format_is_task_prefix(self, repository):
        """Test that SK follows TASK#{id} format"""
        task = create_test_task()
        await repository.save(task)

        response = repository.table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )
        assert response['Item']['SK'] == f'TASK#{TASK_ID_1}'

    @pytest.mark.asyncio
    async def test_gsi1pk_format_is_user_prefix(self, repository):
        """Test that GSI1PK follows USER#{id} format"""
        task = create_test_task()
        await repository.save(task)

        response = repository.table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )
        assert response['Item']['GSI1PK'] == f'USER#{USER_ID_1}'

    @pytest.mark.asyncio
    async def test_gsi1sk_format_contains_timestamp_and_id(self, repository):
        """Test that GSI1SK contains creation timestamp and task ID"""
        task = create_test_task()
        await repository.save(task)

        response = repository.table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )
        gsi1sk = response['Item']['GSI1SK']
        assert gsi1sk.startswith('TASK#')
        assert TASK_ID_1 in gsi1sk

    @pytest.mark.asyncio
    async def test_item_type_is_task(self, repository):
        """Test that saved item has Type attribute set to 'Task'"""
        task = create_test_task()
        await repository.save(task)

        response = repository.table.get_item(
            Key={'PK': f'TASK#{TASK_ID_1}', 'SK': f'TASK#{TASK_ID_1}'}
        )
        assert response['Item']['Type'] == 'Task'
