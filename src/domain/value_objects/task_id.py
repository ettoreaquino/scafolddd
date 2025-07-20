from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class TaskId:
  """Unique identifier for a task."""
  value: str

  def __post_init__(self):
    if not self.value or not isinstance(self.value, str):
      raise ValueError("TaskId cannot be empty")

  @classmethod
  def generate(cls) -> "TaskId":
    """Generate a new unique task id."""
    return cls(f"task-{uuid.uuid4()}")
  
  def __str__(self) -> str:
    return self.value