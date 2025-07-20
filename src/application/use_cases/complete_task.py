from typing import Protocol, Dict, Any, Optional, List
from src.domain.value_objects import TaskId, TaskStatus
from src.domain.repositories import TaskRepository
from src.domain.events import DomainEvent

class EventBus(Protocol):
    """Protocol for event publishing"""
    async def publish(self, events: List[DomainEvent]) -> None:
        pass

class CompleteTaskUseCase:
    """Use case for completing a task"""
    
    def __init__(self, task_repository: TaskRepository, event_bus: EventBus):
        self._task_repository = task_repository
        self._event_bus = event_bus
    
    async def execute(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Execute the complete task use case"""
        
        # Step 1: Validate input
        if not task_id or not task_id.strip():
            raise ValueError("Task ID is required")
        
        # Step 2: Find existing task
        task = await self._task_repository.find_by_id(TaskId(task_id.strip()))
        
        if not task:
            return None  # Task not found
        
        # Step 3: Check business rules (delegate to domain)
        if not task.can_be_completed():
            raise ValueError(f"Task with status '{task.status}' cannot be completed")
        
        # Step 4: Execute domain behavior
        task.update_status(TaskStatus.COMPLETED)
        
        # Step 5: Save changes
        await self._task_repository.save(task)
        
        # Step 6: Publish events
        events = task.pop_events()
        if events:
            await self._event_bus.publish(events)
        
        # Step 7: Return result
        return {
            "task_id": str(task.id),
            "title": task.title,
            "status": str(task.status),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }