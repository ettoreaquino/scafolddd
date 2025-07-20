from datetime import datetime, timezone
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus

def test_domain_setup():
  """Quick verification that domain layer is working"""
  print("🧪 Testing Domain Layer Setup...")

  # Test value objects
  task_id = TaskId.generate()
  user_id = UserId("user-123")
  status = TaskStatus.PENDING
  
  print(f"✅ TaskId generated: {task_id}")
  print(f"✅ UserId created: {user_id}")
  print(f"✅ TaskStatus: {status}")
  
  # Test entity
  task = Task(
      id=task_id,
      user_id=user_id,
      title="Learn Domain Design",
      description="Understand DDD concepts",
      status=status,
      created_at=datetime.now(timezone.utc)
  )
  
  print(f"✅ Created task: {task.title}")
  
  # Test events
  task.update_status(TaskStatus.COMPLETED)
  events = task.pop_events()
  print(f"✅ Generated {len(events)} events")
  
  print("🎉 Domain layer working correctly!")

if __name__ == "__main__":
    test_domain_setup()