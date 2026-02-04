from dependency_injector import containers, providers
from src.infrastructure.repositories import DynamoDBTaskRepository
from src.infrastructure.messaging import SNSEventBus
from src.application.services import (
    CreateTaskService,
    GetTaskService,
    ListTasksService,
    CompleteTaskService
)


class Container(containers.DeclarativeContainer):
    """Dependency injection container"""

    # Configuration
    config = providers.Configuration()

    # Infrastructure
    task_repository = providers.Singleton(
        DynamoDBTaskRepository,
        table_name=config.table_name
    )

    event_bus = providers.Singleton(
        SNSEventBus,
        topic_arn=config.topic_arn
    )

    # Services
    create_task = providers.Factory(
        CreateTaskService,
        task_repository=task_repository,
        event_bus=event_bus
    )

    get_task = providers.Factory(
        GetTaskService,
        task_repository=task_repository
    )

    list_tasks = providers.Factory(
        ListTasksService,
        task_repository=task_repository
    )

    complete_task = providers.Factory(
        CompleteTaskService,
        task_repository=task_repository,
        event_bus=event_bus
    )


def create_container() -> Container:
    """Create and configure the container"""
    container = Container()

    # Load configuration from environment variables
    container.config.table_name.from_env("TABLE_NAME", required=True)
    container.config.topic_arn.from_env("TOPIC_ARN", required=True)

    return container
