from typing import List, Dict, Any
from src.domain.value_objects import UserId
from src.domain.repositories import TaskRepository

class ListTasksUseCase:
    """Use case for listing all tasks for a user"""

    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository

    async def execute(self, user_id: str) -> List[Dict[str, Any]]:
        """Execute the list tasks use case"""

        # Step 1: Validate input
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required")
        
        # Step 2: Find all tasks from user
        tasks = await self._task_repository.find_by_user_id(UserId(user_id.strip()))

        # Step 3: Convert to response format
        return [
            {
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "status": str(task.status),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "user_id": str(task.user_id)
            }
            for task in tasks  # List comprehension to transform each task
        ]