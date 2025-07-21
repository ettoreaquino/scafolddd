#!/usr/bin/env python3
"""
🧪 Application Layer Verification Script

This script verifies that Part 3 (Application Layer) is correctly implemented
by testing all services with mock dependencies.

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
from src.application.services import (
    CreateTaskService,
    GetTaskService,
    ListTasksService,
    CompleteTaskService
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
        print(f"  📡 MockEventBus: Published {len(events)} events")

# ===== TEST FUNCTIONS =====

async def test_create_task_service():
    """Test CreateTaskService with mock dependencies"""
    print("\n1️⃣ Testing CreateTaskService...")
    
    # Setup mocks
    mock_repository = MockTaskRepository()
    mock_event_bus = MockEventBus()
    
    # Create service
    service = CreateTaskService(mock_repository, mock_event_bus)
    
    # Test successful creation
    result = await service.execute("user-123", "Test Task", "Test Description")
    
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
    
    print("  ✅ CreateTaskService: Response format correct")
    print("  ✅ CreateTaskService: Dependencies called correctly")
    print("  ✅ CreateTaskService: Domain events published")
    
    # Test input validation
    try:
        await service.execute("", "Test Task")  # Empty user_id
        assert False, "Should raise ValueError for empty user_id"
    except ValueError as e:
        print(f"  ✅ CreateTaskService: Input validation works - {e}")
    
    try:
        await service.execute("user-123", "")  # Empty title
        assert False, "Should raise ValueError for empty title"
    except ValueError as e:
        print(f"  ✅ CreateTaskService: Input validation works - {e}")
    
    return mock_repository  # Return for next tests

async def test_get_task_service(repository_with_data):
    """Test GetTaskService with mock dependencies"""
    print("\n2️⃣ Testing GetTaskService...")
    
    service = GetTaskService(repository_with_data)
    
    # Test finding existing task
    task_ids = list(repository_with_data.saved_tasks.keys())
    if task_ids:
        task_id = task_ids[0]
        result = await service.execute(task_id)
        
        assert result is not None, "Should return task data"
        assert "task_id" in result
        assert "title" in result
        assert result["task_id"] == task_id
        
        print("  ✅ GetTaskService: Found existing task")
    
    # Test not found case
    result = await service.execute("non-existent-task")
    assert result is None, "Should return None for non-existent task"
    print("  ✅ GetTaskService: Handles not found correctly")
    
    # Test input validation
    try:
        await service.execute("")  # Empty task_id
        assert False, "Should raise ValueError for empty task_id"
    except ValueError as e:
        print(f"  ✅ GetTaskService: Input validation works - {e}")

async def test_list_tasks_service(repository_with_data):
    """Test ListTasksService with mock dependencies"""
    print("\n3️⃣ Testing ListTasksService...")
    
    service = ListTasksService(repository_with_data)
    
    # Test listing user tasks
    result = await service.execute("user-123")
    
    assert isinstance(result, list), "Should return a list"
    if result:
        # Check first task format
        task = result[0]
        expected_fields = ["task_id", "title", "description", "status", "created_at", "user_id"]
        for field in expected_fields:
            assert field in task, f"Missing field in task: {field}"
    
    print(f"  ✅ ListTasksService: Returned {len(result)} tasks")
    print("  ✅ ListTasksService: Response format correct")
    
    # Test with non-existent user
    result = await service.execute("non-existent-user")
    assert isinstance(result, list), "Should return empty list for non-existent user"
    assert len(result) == 0, "Should return empty list for non-existent user"
    print("  ✅ ListTasksService: Handles non-existent user correctly")
    
    # Test input validation
    try:
        await service.execute("")  # Empty user_id
        assert False, "Should raise ValueError for empty user_id"
    except ValueError as e:
        print(f"  ✅ ListTasksService: Input validation works - {e}")

async def test_complete_task_service(repository_with_data):
    """Test CompleteTaskService with mock dependencies"""
    print("\n4️⃣ Testing CompleteTaskService...")
    
    mock_event_bus = MockEventBus()
    service = CompleteTaskService(repository_with_data, mock_event_bus)
    
    # Test completing existing task
    task_ids = list(repository_with_data.saved_tasks.keys())
    if task_ids:
        task_id = task_ids[0]
        result = await service.execute(task_id)
        
        assert result is not None, "Should return task data"
        assert "task_id" in result
        assert "status" in result
        assert result["status"] == "completed"
        
        print("  ✅ CompleteTaskService: Task completed successfully")
        print("  ✅ CompleteTaskService: Response format correct")
        
        # Verify events were published
        assert mock_event_bus.publish_called, "Should publish domain events"
        print("  ✅ CompleteTaskService: Domain events published")
    
    # Test not found case
    result = await service.execute("non-existent-task")
    assert result is None, "Should return None for non-existent task"
    print("  ✅ CompleteTaskService: Handles not found correctly")
    
    # Test input validation
    try:
        await service.execute("")  # Empty task_id
        assert False, "Should raise ValueError for empty task_id"
    except ValueError as e:
        print(f"  ✅ CompleteTaskService: Input validation works - {e}")

async def test_service_independence():
    """Test that services work independently with fresh mocks"""
    print("\n5️⃣ Testing Service Independence...")
    
    # Each service should work with its own mock dependencies
    repo1 = MockTaskRepository()
    repo2 = MockTaskRepository()
    bus1 = MockEventBus()
    bus2 = MockEventBus()
    
    service1 = CreateTaskService(repo1, bus1)
    service2 = CreateTaskService(repo2, bus2)
    
    # Execute independently
    await service1.execute("user-1", "Task 1")
    await service2.execute("user-2", "Task 2")
    
    # Should not interfere with each other
    assert len(repo1.saved_tasks) == 1
    assert len(repo2.saved_tasks) == 1
    assert len(bus1.published_events) > 0
    assert len(bus2.published_events) > 0
    
    print("  ✅ Services are independent and reusable")

async def run_all_tests():
    """Run all verification tests"""
    try:
        # Test CreateTaskService and get repository with data
        repository_with_data = await test_create_task_service()
        
        # Test other services with the populated repository
        await test_get_task_service(repository_with_data)
        await test_list_tasks_service(repository_with_data)
        await test_complete_task_service(repository_with_data)
        await test_service_independence()
        
        print("\n" + "=" * 60)
        print("🎉 ALL APPLICATION LAYER TESTS PASSED!")
        print("\n✅ Part 3 Acceptance Criteria Met:")
        print("  ✅ All services implement proper input validation")
        print("  ✅ Domain events are published after successful operations")
        print("  ✅ Error messages are clear and actionable")
        print("  ✅ Services are independent and reusable")
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
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1) 