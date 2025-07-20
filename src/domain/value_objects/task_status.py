from enum import Enum

class TaskStatus(Enum):
  """Possible states for a task."""
  PENDING = "pending"
  IN_PROGRESS = "in_progress"
  COMPLETED = "completed"
  CANCELLED = "cancelled"

  def __str__(self) -> str:
    return self.value