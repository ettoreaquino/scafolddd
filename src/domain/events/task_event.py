from dataclasses import dataclass
from .base_event import DomainEvent

@dataclass
class TaskCreated(DomainEvent):
  """Event fired when a task is created."""
  task_title: str
  user_id: str

  def to_dict(self) -> dict:
    data = super().to_dict()
    data.update({
      "task_title": self.task_title,
      "user_id": self.user_id,
    })
    return data
  
@dataclass
class TaskCompleted(DomainEvent):
  """Event fired when a task is completed."""
  task_title: str
  user_id: str

  def to_dict(self) -> dict:
    data = super().to_dict()
    data.update({
      "task_title": self.task_title,
      "user_id": self.user_id,
    })
    return data
  
@dataclass
class TaskStatusChanged(DomainEvent):
  """Event fired when a task status is changed."""
  old_status: str
  new_status: str
  user_id: str

  def to_dict(self) -> dict:
    data = super().to_dict()
    data.update({
      "old_status": self.old_status,
      "new_status": self.new_status,
      "user_id": self.user_id,
    })
    return data