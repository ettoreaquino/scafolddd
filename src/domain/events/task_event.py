from datetime import datetime
from .base_event import DomainEvent

class TaskCreated(DomainEvent):
    """Event fired when a task is created."""
    
    def __init__(self, aggregate_id: str, task_title: str, user_id: str, 
                 event_id: str = None, timestamp: datetime = None):
        super().__init__(aggregate_id, event_id, timestamp)
        self.task_title = task_title
        self.user_id = user_id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "task_title": self.task_title,
            "user_id": self.user_id,
        })
        return data
  
class TaskCompleted(DomainEvent):
    """Event fired when a task is completed."""
    
    def __init__(self, aggregate_id: str, task_title: str, user_id: str, 
                 event_id: str = None, timestamp: datetime = None):
        super().__init__(aggregate_id, event_id, timestamp)
        self.task_title = task_title
        self.user_id = user_id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "task_title": self.task_title,
            "user_id": self.user_id,
        })
        return data
  
class TaskStatusChanged(DomainEvent):
    """Event fired when a task status is changed."""
    
    def __init__(self, aggregate_id: str, old_status: str, new_status: str, user_id: str, 
                 event_id: str = None, timestamp: datetime = None):
        super().__init__(aggregate_id, event_id, timestamp)
        self.old_status = old_status
        self.new_status = new_status
        self.user_id = user_id

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "old_status": self.old_status,
            "new_status": self.new_status,
            "user_id": self.user_id,
        })
        return data