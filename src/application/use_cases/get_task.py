from typing import Dict, Any, Optional

from src.domain.value_objects import TaskId
from src.domain.repositories import TaskRepository

class GetTaskUseCase:
    """Use case for retrieving a task by its ID"""

    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository

    async def execute(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Execute the get task use case"""

        # Step 1: Validate input
        if not task_id or not task_id.strip():
            raise ValueError("Task ID is required")
        
        # Step 2: Find task using domain repository
        task = await self._task_repository.find_by_id(TaskId(task_id.strip()))

        # Step 3: Handle not found case
        if not task:
            return None
        
        # Step 4: Return formatted response
        return {
            "task_id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": str(task.status),
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "user_id": str(task.user_id)
        }