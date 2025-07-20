from dataclasses import dataclass

@dataclass(frozen=True)
class UserId:
  """Unique identifier for a user."""
  value: str

  def __post_init__(self):
    if not self.value or not isinstance(self.value, str):
      raise ValueError("UserId must be an non-empty string")
  
  def __str__(self) -> str:
    return self.value