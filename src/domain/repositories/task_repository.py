from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.task import Task
from ..value_objects import TaskId, UserId

class TaskRepository(ABC):
  """Abstract repository for Task operations"""

  @abstractmethod
  async def save(self, task: Task) -> None:
    """Save a task to the repository"""
    pass

  @abstractmethod
  async def find_by_id (self, task_id: TaskId) -> Optional[Task]:
    """Find a task by its id"""
    pass
  
  @abstractmethod
  async def find_by_user_id(self, user_id: UserId) -> List[Task]:
    """Find all tasks for a specific user"""
    pass
  
  @abstractmethod
  async def delete(self, task_id: TaskId) -> bool:
    """Delete a task by ID. Returns True if deleted, False if not found"""
    pass
  
  @abstractmethod
  async def exists(self, task_id: Task) -> bool:
    """Check if a task exists"""
    pass
  