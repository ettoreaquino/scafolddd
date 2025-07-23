from datetime import datetime, timezone
from typing import Protocol, List, Dict, Any

from src.domain.entities import Task
from src.domain.events import DomainEvent
from src.domain.repositories import TaskRepository
from src.domain.value_objects import TaskId, UserId, TaskStatus

class EventBus(Protocol):
    """Protocol for event publishing"""
    async def publish(self, events: List[DomainEvent]) -> None:
        """Publish a list of domain events"""
        pass

class CreateTaskService:
    """Service for creating a new task"""
    
    def __init__(self, task_repository: TaskRepository, event_bus: EventBus):
        self._task_repository = task_repository
        self._event_bus = event_bus

    async def execute(self, user_id: str, title: str, description: str = "") -> Dict[str, Any]:
        """Execute the create task service"""

        # Step 1: Validate the inputs (Application Layer responsibility)
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required")
        
        if not title or not title.strip():
            raise ValueError("Task title is required")
        
        # Step 2: Create domain entity (Domain Layer)
        task = Task(
            id=TaskId.generate(),
            user_id=UserId(user_id.strip()),
            title=title.strip(),
            description=description.strip() if description else "",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        # Step 3: Save to repository (Infrastructure Layer, but abstracted)
        await self._task_repository.save(task)

        # Step 4: Publish domain events (Infrastructure Layer, but abstracted)
        events = task.pop_events()
        if events:
            await self._event_bus.publish(events)

        # Step 5: Return application-layer response
        return {
            "task_id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": str(task.status),
            "created_at": task.created_at.isoformat(),
            "user_id": str(task.user_id)
        }