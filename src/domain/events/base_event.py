from abc import ABC
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

@dataclass
class DomainEvent(ABC):
  """Base class for all domain events."""
  event_id: str
  timestamp: datetime
  aggregate_id: str

  def __post_init__(self):
    if not self.event_id:
      object.__setattr__(self, "event_id", str(uuid.uuid4()))
    if not self.timestamp:
      object.__setattr__(self, "timestamp", datetime.now(timezone.utc))

  def to_dict(self) -> dict:
    """Convert the event to a dictionary."""
    return {
      "event_id": self.event_id,
      "timestamp": self.timestamp,
      "aggregate_id": self.aggregate_id,
      "event_type": self.__class__.__name__,
    }