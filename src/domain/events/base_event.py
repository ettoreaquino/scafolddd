from abc import ABC
from datetime import datetime, timezone
import uuid

class DomainEvent(ABC):
    """Base class for all domain events."""
    
    def __init__(self, aggregate_id: str, event_id: str = None, timestamp: datetime = None):
        self.aggregate_id = aggregate_id
        self.event_id = event_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert the event to a dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "event_type": self.__class__.__name__,
        }