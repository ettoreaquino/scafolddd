import pytest
import os
import boto3
from moto import mock_aws
from src.infrastructure.container import Container, create_container
from src.infrastructure.repositories.dynamodb_task_repository import DynamoDBTaskRepository
from src.infrastructure.messaging.sns_event_bus import SNSEventBus
from src.application.services import (
    CreateTaskService,
    GetTaskService,
    ListTasksService,
    CompleteTaskService,
)


# ============================================================================
# Test Constants
# ============================================================================

TABLE_NAME = "test-tasks"
TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:test-topic"


# ============================================================================
# Helpers
# ============================================================================

def create_dynamodb_table():
    """Create a DynamoDB table for testing"""
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


@pytest.fixture
def mock_aws_env():
    """Create mocked AWS environment with DynamoDB table and SNS topic"""
    with mock_aws():
        create_dynamodb_table()
        sns_client = boto3.client('sns', region_name='us-east-1')
        topic = sns_client.create_topic(Name='test-topic')
        yield topic['TopicArn']


@pytest.fixture
def container(mock_aws_env):
    """Create a configured container with mocked AWS"""
    c = Container()
    c.config.table_name.from_value(TABLE_NAME)
    c.config.topic_arn.from_value(mock_aws_env)
    return c


# ============================================================================
# Test: Container Initialization
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestContainerInitialization:
    """Test container initialization and structure"""

    def test_container_can_be_created(self):
        """Test that container can be instantiated"""
        c = Container()
        assert c is not None

    def test_container_has_config(self):
        """Test that container has a config provider"""
        c = Container()
        assert hasattr(c, 'config')

    def test_container_has_task_repository_provider(self):
        """Test that container has a task_repository provider"""
        c = Container()
        assert hasattr(c, 'task_repository')

    def test_container_has_event_bus_provider(self):
        """Test that container has an event_bus provider"""
        c = Container()
        assert hasattr(c, 'event_bus')

    def test_container_has_create_task_provider(self):
        """Test that container has a create_task service provider"""
        c = Container()
        assert hasattr(c, 'create_task')

    def test_container_has_get_task_provider(self):
        """Test that container has a get_task service provider"""
        c = Container()
        assert hasattr(c, 'get_task')

    def test_container_has_complete_task_provider(self):
        """Test that container has a complete_task service provider"""
        c = Container()
        assert hasattr(c, 'complete_task')

    def test_container_has_list_tasks_provider(self):
        """Test that container has a list_tasks service provider"""
        c = Container()
        assert hasattr(c, 'list_tasks')


# ============================================================================
# Test: Configuration
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestContainerConfiguration:
    """Test container configuration loading"""

    def test_config_table_name(self):
        """Test that table_name config is set correctly"""
        c = Container()
        c.config.table_name.from_value(TABLE_NAME)
        assert c.config.table_name() == TABLE_NAME

    def test_config_topic_arn(self):
        """Test that topic_arn config is set correctly"""
        c = Container()
        c.config.topic_arn.from_value(TOPIC_ARN)
        assert c.config.topic_arn() == TOPIC_ARN

    def test_config_from_environment_variables(self, mock_aws_env):
        """Test that configuration can be loaded from env vars"""
        os.environ['TABLE_NAME'] = TABLE_NAME
        os.environ['TOPIC_ARN'] = mock_aws_env
        try:
            c = create_container()
            assert c.config.table_name() == TABLE_NAME
            assert c.config.topic_arn() == mock_aws_env
        finally:
            del os.environ['TABLE_NAME']
            del os.environ['TOPIC_ARN']


# ============================================================================
# Test: Repository Registration
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestContainerRepositoryRegistration:
    """Test that repository is registered correctly in the container"""

    def test_task_repository_is_dynamodb_repository(self, container):
        """Test that task_repository resolves to DynamoDBTaskRepository"""
        repository = container.task_repository()
        assert isinstance(repository, DynamoDBTaskRepository)

    def test_task_repository_has_correct_table_name(self, container):
        """Test that repository is configured with correct table name"""
        repository = container.task_repository()
        assert repository.table_name == TABLE_NAME

    def test_task_repository_is_singleton(self, container):
        """Test that task_repository returns the same instance"""
        repo1 = container.task_repository()
        repo2 = container.task_repository()
        assert repo1 is repo2


# ============================================================================
# Test: Event Bus Registration
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestContainerEventBusRegistration:
    """Test that event bus is registered correctly in the container"""

    def test_event_bus_is_sns_event_bus(self, container):
        """Test that event_bus resolves to SNSEventBus"""
        event_bus = container.event_bus()
        assert isinstance(event_bus, SNSEventBus)

    def test_event_bus_has_correct_topic_arn(self, container, mock_aws_env):
        """Test that event bus is configured with correct topic ARN"""
        event_bus = container.event_bus()
        assert event_bus.topic_arn == mock_aws_env

    def test_event_bus_is_singleton(self, container):
        """Test that event_bus returns the same instance"""
        bus1 = container.event_bus()
        bus2 = container.event_bus()
        assert bus1 is bus2


# ============================================================================
# Test: Service Registration
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestContainerServiceRegistration:
    """Test that application services are registered correctly"""

    def test_create_task_service_type(self, container):
        """Test that create_task resolves to CreateTaskService"""
        service = container.create_task()
        assert isinstance(service, CreateTaskService)

    def test_get_task_service_type(self, container):
        """Test that get_task resolves to GetTaskService"""
        service = container.get_task()
        assert isinstance(service, GetTaskService)

    def test_list_tasks_service_type(self, container):
        """Test that list_tasks resolves to ListTasksService"""
        service = container.list_tasks()
        assert isinstance(service, ListTasksService)

    def test_complete_task_service_type(self, container):
        """Test that complete_task resolves to CompleteTaskService"""
        service = container.complete_task()
        assert isinstance(service, CompleteTaskService)

    def test_services_are_factory_instances(self, container):
        """Test that services are new instances each time (factory pattern)"""
        service1 = container.create_task()
        service2 = container.create_task()
        assert service1 is not service2


# ============================================================================
# Test: Dependency Wiring
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestContainerDependencyWiring:
    """Test that services are wired with correct dependencies"""

    def test_create_task_has_repository(self, container):
        """Test that CreateTaskService receives task_repository"""
        service = container.create_task()
        assert service._task_repository is not None
        assert isinstance(service._task_repository, DynamoDBTaskRepository)

    def test_create_task_has_event_bus(self, container):
        """Test that CreateTaskService receives event_bus"""
        service = container.create_task()
        assert service._event_bus is not None
        assert isinstance(service._event_bus, SNSEventBus)

    def test_get_task_has_repository(self, container):
        """Test that GetTaskService receives task_repository"""
        service = container.get_task()
        assert service._task_repository is not None
        assert isinstance(service._task_repository, DynamoDBTaskRepository)

    def test_list_tasks_has_repository(self, container):
        """Test that ListTasksService receives task_repository"""
        service = container.list_tasks()
        assert service._task_repository is not None
        assert isinstance(service._task_repository, DynamoDBTaskRepository)

    def test_complete_task_has_repository(self, container):
        """Test that CompleteTaskService receives task_repository"""
        service = container.complete_task()
        assert service._task_repository is not None
        assert isinstance(service._task_repository, DynamoDBTaskRepository)

    def test_complete_task_has_event_bus(self, container):
        """Test that CompleteTaskService receives event_bus"""
        service = container.complete_task()
        assert service._event_bus is not None
        assert isinstance(service._event_bus, SNSEventBus)

    def test_services_share_same_repository(self, container):
        """Test that all services share the same repository singleton"""
        create_svc = container.create_task()
        get_svc = container.get_task()
        list_svc = container.list_tasks()
        complete_svc = container.complete_task()

        assert create_svc._task_repository is get_svc._task_repository
        assert get_svc._task_repository is list_svc._task_repository
        assert list_svc._task_repository is complete_svc._task_repository

    def test_services_share_same_event_bus(self, container):
        """Test that services that use event_bus share the same singleton"""
        create_svc = container.create_task()
        complete_svc = container.complete_task()

        assert create_svc._event_bus is complete_svc._event_bus


# ============================================================================
# Test: create_container Factory Function
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestCreateContainerFunction:
    """Test the create_container factory function"""

    def test_create_container_returns_container(self, mock_aws_env):
        """Test that create_container returns a Container instance"""
        os.environ['TABLE_NAME'] = TABLE_NAME
        os.environ['TOPIC_ARN'] = mock_aws_env
        try:
            c = create_container()
            assert c is not None
            assert hasattr(c, 'config')
            assert hasattr(c, 'task_repository')
            assert hasattr(c, 'event_bus')
        finally:
            del os.environ['TABLE_NAME']
            del os.environ['TOPIC_ARN']

    def test_create_container_loads_env_config(self, mock_aws_env):
        """Test that create_container loads config from env"""
        os.environ['TABLE_NAME'] = TABLE_NAME
        os.environ['TOPIC_ARN'] = mock_aws_env
        try:
            c = create_container()
            assert c.config.table_name() == TABLE_NAME
            assert c.config.topic_arn() == mock_aws_env
        finally:
            del os.environ['TABLE_NAME']
            del os.environ['TOPIC_ARN']
