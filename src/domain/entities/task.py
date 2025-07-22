from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from ..value_objects import TaskId, UserId, TaskStatus
from ..events import DomainEvent, TaskCreated, TaskCompleted, TaskStatusChanged

@dataclass
class Task:
  """A task entity representing a user's task."""
  id: TaskId
  user_id: UserId
  title: str
  description: str
  status: TaskStatus
  created_at: datetime
  updated_at: Optional[datetime] = None
  completed_at: Optional[datetime] = None
  _events: List[DomainEvent] = field(default_factory=list, init=False)

  def __post_init__(self):
    """Validate task after creation"""
    if not self.title or len(self.title.strip()) == 0:
      raise ValueError("Task title cannot be empty")
    if len(self.title) > 200:
      raise ValueError("Task title cannot be longer than 200 characters")
    
    # Fire creation event for new tasks
    if self.status == TaskStatus.PENDING:
      self._events.append(TaskCreated(
        event_id="",
        timestamp=self.created_at,
        aggregate_id=str(self.id),
        task_title=self.title,
        user_id=str(self.user_id)
      ))

  def update_status(self, new_status: TaskStatus) -> None:
    """Update task status and fire appropriate events"""
    if self.status == new_status:
      return # No change needed
    
    old_status = self.status
    self.status = new_status
    self.updated_at = datetime.now(timezone.utc)

    # Set completed_at when task is completed
    if new_status == TaskStatus.COMPLETED:
      self.completed_at = self.updated_at

    # Fire status change event
    self._events.append(TaskStatusChanged(
      event_id="",
      timestamp=self.updated_at,
      aggregate_id=str(self.id),
      old_status=str(old_status),
      new_status=str(new_status),
      user_id=str(self.user_id)
    ))

    # Fire completion event if task is completed
    if new_status == TaskStatus.COMPLETED:
      self._events.append(TaskCompleted(
        event_id="",
        timestamp=self.updated_at,
        aggregate_id=str(self.id),
        task_title=self.title,
        user_id=str(self.user_id)
      ))

  def update_details(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
    """Update task title and/or description"""
    if title is not None:
      if not title or len(title.strip()) == 0:
        raise ValueError("Task title cannot be empty")
      if len(title) > 200:
        raise ValueError("Task title cannot exceed 200 characters")
      self.title = title

    if description is not None:
      self.description = description

    self.updated_at = datetime.now(timezone.utc)

  def pop_events(self) -> List[DomainEvent]:
    """Return and clear all domain events"""
    events = self._events.copy()
    self._events.clear()
    return events
  
  def is_completed(self) -> bool:
    """Check if task is completed"""
    return self.status == TaskStatus.COMPLETED
  
  def can_be_completed(self) -> bool:
    """Check if task can be completed"""
    return self.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]