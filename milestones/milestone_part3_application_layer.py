#!/usr/bin/env python3
"""
🧪 Application Layer Verification Script

This script verifies that Part 3 (Application Layer) is correctly implemented
by testing all use cases with mock dependencies.

Run with: poetry run python test_application_verification.py
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import Mock, AsyncMock

# Import our domain and application layers
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus
from src.domain.events import DomainEvent, TaskCreated, TaskCompleted
from src.application.use_cases import (
    CreateTaskUseCase,
    GetTaskUseCase,
    ListTasksUseCase,
    CompleteTaskUseCase
)

print("🧪 Starting Application Layer Verification...")
print("=" * 60)

# ===== MOCK IMPLEMENTATIONS =====

class MockTaskRepository:
    """Mock implementation of TaskRepository for testing"""
    
    def __init__(self):
        self.saved_tasks = {}
        self.save_called = False
        
    async def save(self, task: Task) -> None:
        """Mock save - stores task in memory"""
        self.save_called = True
        self.saved_tasks[str(task.id)] = task
        print(f"  📝 MockRepository: Saved task '{task.title}' (ID: {task.id})")
    
    async def find_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Mock find by ID"""
        task = self.saved_tasks.get(str(task_id))
        if task:
            print(f"  🔍 MockRepository: Found task '{task.title}'")
        else:
            print(f"  ❌ MockRepository: Task {task_id} not found")
        return task
    
    async def find_by_user_id(self, user_id: UserId) -> List[Task]:
        """Mock find by user ID"""
        user_tasks = [task for task in self.saved_tasks.values() 
                     if task.user_id == user_id]
        print(f"  📋 MockRepository: Found {len(user_tasks)} tasks for user {user_id}")
        return user_tasks

class MockEventBus:
    """Mock implementation of EventBus for testing"""
    
    def __init__(self):
        self.published_events = []
        self.publish_called = False
    
    async def publish(self, events: List[DomainEvent]) -> None:
        """Mock publish - stores events in memory"""
        self.publish_called = True
        self.published_events.extend(events)
        for event in events:
            print(f"  📢 MockEventBus: Published {event.__class__.__name__}")

# ===== TEST FUNCTIONS =====

async def test_create_task_use_case():
    """Test CreateTaskUseCase with mock dependencies"""
    print("\n1️⃣ Testing CreateTaskUseCase...")
    
    # Setup mocks
    mock_repository = MockTaskRepository()
    mock_event_bus = MockEventBus()
    
    # Create use case
    use_case = CreateTaskUseCase(mock_repository, mock_event_bus)
    
    # Test successful creation
    result = await use_case.execute("user-123", "Test Task", "Test Description")
    
    # Verify response format
    expected_fields = ["task_id", "title", "description", "status", "created_at", "user_id"]
    for field in expected_fields:
        assert field in result, f"Missing field: {field}"
    
    assert result["title"] == "Test Task"
    assert result["description"] == "Test Description"
    assert result["status"] == "pending"
    assert result["user_id"] == "user-123"
    
    # Verify mocks were called
    assert mock_repository.save_called, "Repository.save() should be called"
    assert mock_event_bus.publish_called, "EventBus.publish() should be called"
    assert len(mock_event_bus.published_events) > 0, "Should publish domain events"
    
    print("  ✅ CreateTaskUseCase: Response format correct")
    print("  ✅ CreateTaskUseCase: Dependencies called correctly")
    print("  ✅ CreateTaskUseCase: Domain events published")
    
    # Test input validation
    try:
        await use_case.execute("", "Test Task")  # Empty user_id
        assert False, "Should raise ValueError for empty user_id"
    except ValueError as e:
        print(f"  ✅ CreateTaskUseCase: Input validation works - {e}")
    
    try:
        await use_case.execute("user-123", "")  # Empty title
        assert False, "Should raise ValueError for empty title"
    except ValueError as e:
        print(f"  ✅ CreateTaskUseCase: Input validation works - {e}")
    
    return mock_repository  # Return for next tests

async def test_get_task_use_case(repository_with_data):
    """Test GetTaskUseCase with mock dependencies"""
    print("\n2️⃣ Testing GetTaskUseCase...")
    
    use_case = GetTaskUseCase(repository_with_data)
    
    # Test finding existing task
    task_ids = list(repository_with_data.saved_tasks.keys())
    if task_ids:
        task_id = task_ids[0]
        result = await use_case.execute(task_id)
        
        assert result is not None, "Should return task data"
        assert "task_id" in result
        assert "title" in result
        assert result["task_id"] == task_id
        
        print("  ✅ GetTaskUseCase: Found existing task")
    
    # Test not found case
    result = await use_case.execute("non-existent-task")
    assert result is None, "Should return None for non-existent task"
    print("  ✅ GetTaskUseCase: Handles not found correctly")
    
    # Test input validation
    try:
        await use_case.execute("")  # Empty task_id
        assert False, "Should raise ValueError for empty task_id"
    except ValueError as e:
        print(f"  ✅ GetTaskUseCase: Input validation works - {e}")

async def test_list_tasks_use_case(repository_with_data):
    """Test ListTasksUseCase with mock dependencies"""
    print("\n3️⃣ Testing ListTasksUseCase...")
    
    use_case = ListTasksUseCase(repository_with_data)
    
    # Test listing user tasks
    result = await use_case.execute("user-123")
    
    assert isinstance(result, list), "Should return a list"
    if result:
        # Check first task format
        task = result[0]
        expected_fields = ["task_id", "title", "description", "status", "created_at", "user_id"]
        for field in expected_fields:
            assert field in task, f"Missing field in task: {field}"
    
    print(f"  ✅ ListTasksUseCase: Returned {len(result)} tasks")
    print("  ✅ ListTasksUseCase: Response format correct")
    
    # Test with non-existent user
    result = await use_case.execute("non-existent-user")
    assert isinstance(result, list), "Should return empty list for non-existent user"
    assert len(result) == 0, "Should return empty list for non-existent user"
    print("  ✅ ListTasksUseCase: Handles non-existent user correctly")
    
    # Test input validation
    try:
        await use_case.execute("")  # Empty user_id
        assert False, "Should raise ValueError for empty user_id"
    except ValueError as e:
        print(f"  ✅ ListTasksUseCase: Input validation works - {e}")

async def test_complete_task_use_case(repository_with_data):
    """Test CompleteTaskUseCase with mock dependencies"""
    print("\n4️⃣ Testing CompleteTaskUseCase...")
    
    mock_event_bus = MockEventBus()
    use_case = CompleteTaskUseCase(repository_with_data, mock_event_bus)
    
    # Test completing existing task
    task_ids = list(repository_with_data.saved_tasks.keys())
    if task_ids:
        task_id = task_ids[0]
        result = await use_case.execute(task_id)
        
        assert result is not None, "Should return task data"
        assert result["status"] == "completed", "Task should be marked as completed"
        assert "completed_at" in result, "Should include completion timestamp"
        
        print("  ✅ CompleteTaskUseCase: Task completed successfully")
        print("  ✅ CompleteTaskUseCase: Response format correct")
        
        # Verify events were published
        assert mock_event_bus.publish_called, "Should publish completion events"
        assert len(mock_event_bus.published_events) > 0, "Should have published events"
        print("  ✅ CompleteTaskUseCase: Domain events published")
    
    # Test not found case
    result = await use_case.execute("non-existent-task")
    assert result is None, "Should return None for non-existent task"
    print("  ✅ CompleteTaskUseCase: Handles not found correctly")
    
    # Test input validation
    try:
        await use_case.execute("")  # Empty task_id
        assert False, "Should raise ValueError for empty task_id"
    except ValueError as e:
        print(f"  ✅ CompleteTaskUseCase: Input validation works - {e}")

async def test_use_case_independence():
    """Test that use cases work independently with fresh mocks"""
    print("\n5️⃣ Testing Use Case Independence...")
    
    # Each use case should work with its own mock dependencies
    repo1 = MockTaskRepository()
    repo2 = MockTaskRepository()
    bus1 = MockEventBus()
    bus2 = MockEventBus()
    
    use_case1 = CreateTaskUseCase(repo1, bus1)
    use_case2 = CreateTaskUseCase(repo2, bus2)
    
    # Execute independently
    await use_case1.execute("user-1", "Task 1")
    await use_case2.execute("user-2", "Task 2")
    
    # Should not interfere with each other
    assert len(repo1.saved_tasks) == 1
    assert len(repo2.saved_tasks) == 1
    assert len(bus1.published_events) > 0
    assert len(bus2.published_events) > 0
    
    print("  ✅ Use cases are independent and reusable")

async def run_all_tests():
    """Run all verification tests"""
    try:
        # Test CreateTaskUseCase and get repository with data
        repository_with_data = await test_create_task_use_case()
        
        # Test other use cases with the populated repository
        await test_get_task_use_case(repository_with_data)
        await test_list_tasks_use_case(repository_with_data)
        await test_complete_task_use_case(repository_with_data)
        await test_use_case_independence()
        
        print("\n" + "=" * 60)
        print("🎉 ALL APPLICATION LAYER TESTS PASSED!")
        print("\n✅ Part 3 Acceptance Criteria Met:")
        print("  ✅ All use cases implement proper input validation")
        print("  ✅ Domain events are published after successful operations")
        print("  ✅ Error messages are clear and actionable")
        print("  ✅ Use cases are independent and reusable")
        print("  ✅ Response format is consistent across all operations")
        print("  ✅ Dependencies are injected via constructor")
        print("\n🚀 Ready to proceed to Part 4: Infrastructure Layer!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run verification
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1) 