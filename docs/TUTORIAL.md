# Backend Tutorial - Serverless Python API with CDK

> **A comprehensive guide to building production-ready serverless Python backends using Domain Driven Design, CLEAN Architecture, and AWS CDK.**

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Setup](#project-setup)
- [Domain Layer Implementation](#domain-layer-implementation)
- [Application Layer Implementation](#application-layer-implementation)
- [Infrastructure Layer Implementation](#infrastructure-layer-implementation)
- [API Adapter Layer Implementation](#api-adapter-layer-implementation)
- [CDK Infrastructure Implementation](#cdk-infrastructure-implementation)
- [Testing Implementation](#testing-implementation)
- [Deployment and Testing](#deployment-and-testing)
- [Production Readiness](#production-readiness)
- [API Documentation](#api-documentation)
- [Next Steps](#next-steps)

---

## 📖 Overview

This tutorial demonstrates how to build a **Task Management API** using serverless architecture on AWS. The project showcases industry best practices including:

- **Domain Driven Design (DDD)** - Clean separation of business logic
- **CLEAN Architecture** - Maintainable and testable code structure
- **SOLID Principles** - Proper dependency management and abstractions
- **Event-Driven Architecture** - Asynchronous processing with SNS/SQS
- **Infrastructure as Code** - AWS CDK with Python

### 🎯 What You'll Build

A complete REST API for task management with:
- ✅ Create, read, update, and complete tasks
- ✅ Event-driven notifications
- ✅ Production-ready monitoring and logging
- ✅ Comprehensive testing suite
- ✅ Swagger API documentation

### 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │     Lambda      │    │    DynamoDB     │
│                 │───>│   Functions     │───>│     Table       │
│   + Swagger     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SNS Topic     │───>│   SQS Queue     │
                       │                 │    │   + Lambda      │
                       └─────────────────┘    └─────────────────┘
```

### 🗄️ DynamoDB Table Design

The tutorial uses a **single-table design** following DynamoDB best practices for optimal performance and cost efficiency:

```
┌────────────────────────────────────────────────────────────────┐
│                         DynamoDB Table                         │
│                                                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │     Task        │────│   TaskId (PK)   │────│ TASK#{id}   │ │
│  │   Entity        │    │   TaskId (SK)   │    │ TASK#{id}   │ │
│  │                 │    └─────────────────┘    └─────────────┘ │
│  │ • title         │                                           │
│  │ • description   │    ┌─────────────────┐    ┌─────────────┐ │
│  │ • status        │────│ UserId (GSI1PK) │────│ USER#{id}   │ │
│  │ • created_at    │    │Created (GSI1SK) │    │TASK#{date}  │ │
│  │ • updated_at    │    └─────────────────┘    └─────────────┘ │
│  │ • completed_at  │                                           │
│  └─────────────────┘              GSI1                         │
└────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UserId        │    │     TaskId      │    │   TaskStatus    │
│ Value Object    │    │  Value Object   │    │  Value Object   │
│                 │    │                 │    │                 │
│ • value: string │    │ • value: string │    │ • PENDING       │
│ • validation    │    │ • generate()    │    │ • IN_PROGRESS   │
│                 │    │ • validation    │    │ • COMPLETED     │
└─────────────────┘    └─────────────────┘    │ • CANCELLED     │
                                              └─────────────────┘
```

**Access Patterns:**
- **Get Task by ID**: Query `PK = TASK#{task_id}` and `SK = TASK#{task_id}`
- **List User Tasks**: Query GSI1 with `GSI1PK = USER#{user_id}` (sorted by creation date)
- **Delete Task**: Delete item with `PK = TASK#{task_id}` and `SK = TASK#{task_id}`

**Key Design Benefits:**
- ✅ **Single-table design** reduces costs and improves performance
- ✅ **Predictable access patterns** with O(1) lookups
- ✅ **Efficient user queries** via GSI1 with automatic sorting
- ✅ **Domain-driven value objects** ensure data consistency

---

## 🔧 Prerequisites

Ensure your development environment has:

- ✅ Python 3.12
- ✅ Poetry (package manager)
- ✅ Node.js (for CDK)
- ✅ AWS CLI configured with appropriate credentials
- ✅ AWS CDK CLI (`npm install -g aws-cdk`)

**Quick verification:**
```bash
python3.12 --version
poetry --version
node --version
aws --version
cdk --version
```

---

## 🚀 Project Setup

### Step 1: Initialize Project Structure

```bash
# Create project directory
mkdir scafolddd
cd scafolddd

# Create pyproject.toml file directly (more reliable than poetry init)
cat > pyproject.toml << 'EOF'
[project]
name = "scafolddd"
version = "0.1.0"
description = ""
authors = [
    {name = "ettore.aquino",email = "ettore@ettoreaquino.com"}
]
readme = "README.md"
requires-python = ">=3.12,<4.0.0"

[tool.poetry]
packages = [{include = "scafolddd", from = "src"}]

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
EOF

# Verify the file was created
cat pyproject.toml
```

**✅ Verification:** You should see the `pyproject.toml` file contents displayed. 

**Alternative method** (if the above doesn't work):
```bash
# Create the file manually with your text editor
nano pyproject.toml
# or
vim pyproject.toml
# or
code pyproject.toml
```

Then copy and paste the content from above into the file.

### Step 2: Add Dependencies

```bash
# Production dependencies
poetry add boto3 pydantic aws-lambda-powertools dependency-injector

# Development dependencies
poetry add --group dev pytest pytest-asyncio pytest-cov pytest-mock moto black isort mypy pre-commit

# CDK dependencies
poetry add --group dev aws-cdk-lib constructs
```

### Step 3: Create Directory Structure

```bash
# Create complete directory structure
mkdir -p src/{domain/{entities,value_objects,services,repositories,events,exceptions},application/{services,commands,queries,handlers},infrastructure/{repositories,messaging,email},adapters/{api,events},commons/{config,utils,decorators}}

mkdir -p tests/{unit,integration,e2e}
mkdir -p infrastructure/cdk
mkdir -p scripts
mkdir -p docs

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

**Final project structure:**
```
backend-tutorial/
├── src/
│   ├── domain/                    # Pure business logic
│   │   ├── entities/              # Business entities
│   │   ├── value_objects/         # Immutable domain objects
│   │   ├── services/              # Domain services
│   │   ├── repositories/          # Abstract repository interfaces
│   │   ├── events/                # Domain events
│   │   └── exceptions/            # Domain-specific exceptions
│   ├── application/               # Application orchestration
│   │   ├── services/              # Business service implementations
│   │   ├── commands/              # Command objects for CQRS
│   │   ├── queries/               # Query objects for CQRS
│   │   └── handlers/              # Command and query handlers
│   ├── infrastructure/            # External dependencies
│   │   ├── repositories/          # DynamoDB repository implementations
│   │   ├── messaging/             # SNS/SQS adapters
│   │   └── email/                 # SES adapters
│   ├── adapters/                  # Entry points and interfaces
│   │   ├── api/                   # API Gateway Lambda handlers
│   │   └── events/                # Event-driven Lambda handlers
│   └── commons/                   # Common utilities
│       ├── config/                # Environment configuration
│       ├── utils/                 # Common utilities
│       └── decorators/            # Common decorators
├── tests/
├── infrastructure/cdk/            # CDK Python infrastructure
├── docs/                          # API documentation
└── scripts/                       # Deployment and utility scripts
```

---

## 🏛️ Domain Layer Implementation

> **The domain layer contains pure business logic with no external dependencies.**

### Step 4: Create Value Objects

**Value Objects** are immutable objects that represent simple domain concepts.

```python
# src/domain/value_objects/task_id.py
from dataclasses import dataclass
import uuid

@dataclass(frozen=True)
class TaskId:
    """Unique identifier for a task"""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TaskId must be a non-empty string")
    
    @classmethod
    def generate(cls) -> "TaskId":
        """Generate a new unique task ID"""
        return cls(f"task-{uuid.uuid4()}")
    
    def __str__(self) -> str:
        return self.value
```

```python
# src/domain/value_objects/user_id.py
from dataclasses import dataclass

@dataclass(frozen=True)
class UserId:
    """Unique identifier for a user"""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("UserId must be a non-empty string")
    
    def __str__(self) -> str:
        return self.value
```

```python
# src/domain/value_objects/task_status.py
from enum import Enum

class TaskStatus(Enum):
    """Possible states for a task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    def __str__(self) -> str:
        return self.value
```

```python
# src/domain/value_objects/__init__.py
from .task_id import TaskId
from .user_id import UserId
from .task_status import TaskStatus

__all__ = ["TaskId", "UserId", "TaskStatus"]
```

### Step 5: Create Domain Events

**Domain Events** represent important business occurrences.

```python
# src/domain/events/base_event.py
from abc import ABC
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

@dataclass
class DomainEvent(ABC):
    """Base class for all domain events"""
    event_id: str
    timestamp: datetime
    aggregate_id: str
    
    def __post_init__(self):
        if not self.event_id:
            object.__setattr__(self, 'event_id', str(uuid.uuid4()))
        if not self.timestamp:
            object.__setattr__(self, 'timestamp', datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'aggregate_id': self.aggregate_id,
            'event_type': self.__class__.__name__
        }
```

```python
# src/domain/events/task_event.py
from dataclasses import dataclass
from .base_event import DomainEvent

@dataclass
class TaskCreated(DomainEvent):
    """Event fired when a task is created"""
    task_title: str
    user_id: str
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            'task_title': self.task_title,
            'user_id': self.user_id
        })
        return data

@dataclass
class TaskCompleted(DomainEvent):
    """Event fired when a task is completed"""
    task_title: str
    user_id: str
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            'task_title': self.task_title,
            'user_id': self.user_id
        })
        return data

@dataclass
class TaskStatusChanged(DomainEvent):
    """Event fired when task status changes"""
    old_status: str
    new_status: str
    user_id: str
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            'old_status': self.old_status,
            'new_status': self.new_status,
            'user_id': self.user_id
        })
        return data
```

```python
# src/domain/events/__init__.py
from .base_event import DomainEvent
from .task_event import TaskCreated, TaskCompleted, TaskStatusChanged

__all__ = ['DomainEvent', 'TaskCreated', 'TaskCompleted', 'TaskStatusChanged']
```

### Step 6: Create Domain Entity

**Entities** are the main business objects with identity and behavior.

```python
# src/domain/entities/task.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from ..value_objects import TaskId, UserId, TaskStatus
from ..events import DomainEvent, TaskCreated, TaskCompleted, TaskStatusChanged

@dataclass
class Task:
    """Task entity representing a user's task"""
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
            raise ValueError("Task title cannot exceed 200 characters")
        
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
            return  # No change needed
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
        # Fire status changed event
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
            self.completed_at = self.updated_at
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
            self.title = title.strip()
        
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
        """Check if task can be marked as completed"""
        return self.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
```

```python
# src/domain/entities/__init__.py
from .task import Task

__all__ = ['Task']
```

### Step 7: Create Repository Interface

**Repository** abstracts data access without exposing database details.

```python
# src/domain/repositories/task_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Task
from ..value_objects import TaskId, UserId

class TaskRepository(ABC):
    """Abstract repository for Task operations"""
    
    @abstractmethod
    async def save(self, task: Task) -> None:
        """Save a task to the repository"""
        pass
    
    @abstractmethod
    async def find_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Find a task by its ID"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: UserId) -> List[Task]:
        """Find all tasks for a specific user"""
        pass
    
    @abstractmethod
    async def delete(self, task_id: TaskId) -> bool:
        """Delete a task by ID. Returns True if deleted, False if not found"""
        pass
    
    @abstractmethod
    async def exists(self, task_id: TaskId) -> bool:
        """Check if a task exists"""
        pass
```

```python
# src/domain/repositories/__init__.py
from .task_repository import TaskRepository

__all__ = ['TaskRepository']
```

**✅ Test Domain Layer:**

This is a **quick verification script** to ensure your domain layer is working correctly before moving forward. Create this as a temporary test file:

```python
# test_domain_verification.py (create in project root - temporary file)
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
```

**Run the verification:**
```bash
# Run from project root
poetry run python test_domain_verification.py

# Clean up after verification
rm test_domain_verification.py
```

**✅ Expected Output:**
```
🧪 Testing Domain Layer Setup...
✅ TaskId generated: task-123e4567-e89b-12d3-a456-426614174000
✅ UserId created: user-123
✅ TaskStatus: pending
✅ Created task: Learn Domain Design
✅ Generated 3 events
🎉 Domain layer working correctly!
```

> **Note:** This is a **temporary verification script**, not a unit test. We'll create proper unit tests later in the [Testing Implementation](#testing-implementation) section.

---

## 🎯 Application Layer Implementation

> **The application layer orchestrates domain objects and coordinates with infrastructure.**

### Step 8: Create Services

```python
# src/application/services/create_task.py
from datetime import datetime, timezone
from typing import Protocol, Dict, Any, List
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus
from src.domain.repositories import TaskRepository
from src.domain.events import DomainEvent

class EventBus(Protocol):
    """Protocol for event publishing"""
    async def publish(self, events: List[DomainEvent]) -> None:
        """Publish a list of domain events"""
        pass

class CreateTaskService:
    """Service for creating a new task"""
    
    def __init__(self, task_repository: TaskRepository, event_bus: EventBus):
        self._task_repository = task_repository
        self._event_bus = event_bus
    
    async def execute(self, user_id: str, title: str, description: str = "") -> Dict[str, Any]:
        """Execute the create task service"""
        
        # Validate inputs
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required")
        
        if not title or not title.strip():
            raise ValueError("Task title is required")
        
        # Create task entity
        task = Task(
            id=TaskId.generate(),
            user_id=UserId(user_id.strip()),
            title=title.strip(),
            description=description.strip() if description else "",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Save task
        await self._task_repository.save(task)
        
        # Publish events
        events = task.pop_events()
        if events:
            await self._event_bus.publish(events)
        
        # Return result
        return {
            "task_id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": str(task.status),
            "created_at": task.created_at.isoformat(),
            "user_id": str(task.user_id)
        }
```

```python
# src/application/services/get_task.py
from typing import Dict, Any, Optional
from src.domain.value_objects import TaskId
from src.domain.repositories import TaskRepository

class GetTaskService:
    """Service for retrieving a task by ID"""
    
    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository
    
    async def execute(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Execute the get task service"""
        
        if not task_id or not task_id.strip():
            raise ValueError("Task ID is required")
        
        # Find task
        task = await self._task_repository.find_by_id(TaskId(task_id.strip()))
        
        if not task:
            return None
        
        # Return task data
        return {
            "task_id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": str(task.status),
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "user_id": str(task.user_id)
        }
```

```python
# src/application/services/complete_task.py
from typing import Protocol, Dict, Any, Optional, List
from src.domain.value_objects import TaskId, TaskStatus
from src.domain.repositories import TaskRepository
from src.domain.events import DomainEvent

class EventBus(Protocol):
    """Protocol for event publishing"""
    async def publish(self, events: List[DomainEvent]) -> None:
        """Publish a list of domain events"""
        pass

class CompleteTaskService:
    """Service for completing a task"""
    
    def __init__(self, task_repository: TaskRepository, event_bus: EventBus):
        self._task_repository = task_repository
        self._event_bus = event_bus
    
    async def execute(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Execute the complete task service"""
        
        if not task_id or not task_id.strip():
            raise ValueError("Task ID is required")
        
        # Find task
        task = await self._task_repository.find_by_id(TaskId(task_id.strip()))
        
        if not task:
            return None
        
        # Check if task can be completed
        if not task.can_be_completed():
            raise ValueError(f"Task with status '{task.status}' cannot be completed")
        
        # Complete the task
        task.update_status(TaskStatus.COMPLETED)
        
        # Save task
        await self._task_repository.save(task)
        
        # Publish events
        events = task.pop_events()
        if events:
            await self._event_bus.publish(events)
        
        # Return result
        return {
            "task_id": str(task.id),
            "title": task.title,
            "status": str(task.status),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
```

**Create remaining services:**

```python
# src/application/services/list_tasks.py
from typing import List, Dict, Any
from src.domain.value_objects import UserId
from src.domain.repositories import TaskRepository

class ListTasksService:
    """Service for listing all tasks for a user"""
    
    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository
    
    async def execute(self, user_id: str) -> List[Dict[str, Any]]:
        """Execute the list tasks service"""
        
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required")
        
        # Find all tasks for user
        tasks = await self._task_repository.find_by_user_id(UserId(user_id.strip()))
        
        # Convert to response format
        return [
            {
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "status": str(task.status),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "user_id": str(task.user_id)
            }
            for task in tasks
        ]
```

```python
# src/application/services/__init__.py
from .create_task import CreateTaskService
from .get_task import GetTaskService
from .list_tasks import ListTasksService
from .complete_task import CompleteTaskService

__all__ = [
    "CreateTaskService",
    "GetTaskService", 
    "ListTasksService",
    "CompleteTaskService"
]
```

**✅ Verify Application Layer Implementation:**

Create a simple verification script to test that your Application Layer is working correctly:

```python
# test_application_verification.py (temporary file in project root)
import asyncio
from unittest.mock import Mock, AsyncMock
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus
from src.application.services import CreateTaskService

async def test_application_layer():
    """Quick verification that application layer is working"""
    print("🧪 Testing Application Layer Setup...")
    
    # Create mock dependencies
    mock_repository = AsyncMock()
    mock_event_bus = AsyncMock()
    
    # Create service
    service = CreateTaskService(mock_repository, mock_event_bus)
    
    # Test execution
    result = await service.execute("user-123", "Test Task", "Test Description")
    
    # Verify response format
    assert "task_id" in result
    assert result["title"] == "Test Task"
    assert result["status"] == "pending"
    
    # Verify mocks were called
    assert mock_repository.save.called
    assert mock_event_bus.publish.called
    
    print("✅ CreateTaskService working correctly")
    print("✅ Response format correct")
    print("✅ Dependencies called properly")
    print("🎉 Application layer working correctly!")

if __name__ == "__main__":
    asyncio.run(test_application_layer())
```

**Run the verification:**
```bash
poetry run python test_application_verification.py

# Clean up after verification
rm test_application_verification.py
```

**✅ Expected Output:**
```
🧪 Testing Application Layer Setup...
✅ CreateTaskService working correctly
✅ Response format correct
✅ Dependencies called properly
🎉 Application layer working correctly!
```

---

## 🏗️ Infrastructure Layer Implementation

> **The infrastructure layer implements concrete adapters for external services.**

### Step 9: Create DynamoDB Repository

```python
# src/infrastructure/repositories/dynamodb_task_repository.py
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone
from typing import List, Optional
from src.domain.repositories import TaskRepository
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus

class DynamoDBTaskRepository(TaskRepository):
    """DynamoDB implementation of TaskRepository"""
    
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    async def save(self, task: Task) -> None:
        """Save task to DynamoDB using single-table design"""
        item = {
            'PK': f'TASK#{task.id}',
            'SK': f'TASK#{task.id}',
            'GSI1PK': f'USER#{task.user_id}',
            'GSI1SK': f'TASK#{task.created_at.isoformat()}#{task.id}',
            'Type': 'Task',
            'TaskId': str(task.id),
            'UserId': str(task.user_id),
            'Title': task.title,
            'Description': task.description,
            'Status': str(task.status),
            'CreatedAt': task.created_at.isoformat(),
            'UpdatedAt': task.updated_at.isoformat() if task.updated_at else None,
            'CompletedAt': task.completed_at.isoformat() if task.completed_at else None
        }
        
        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}
        
        self.table.put_item(Item=item)
    
    async def find_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Find task by ID"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'TASK#{task_id}',
                    'SK': f'TASK#{task_id}'
                }
            )
            
            if 'Item' in response:
                return self._map_to_entity(response['Item'])
            
            return None
            
        except Exception as e:
            print(f"Error finding task by ID: {e}")
            return None
    
    async def find_by_user_id(self, user_id: UserId) -> List[Task]:
        """Find all tasks for a user"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq(f'USER#{user_id}'),
                ScanIndexForward=False  # Most recent first
            )
            
            return [self._map_to_entity(item) for item in response['Items']]
            
        except Exception as e:
            print(f"Error finding tasks by user ID: {e}")
            return []
    
    async def delete(self, task_id: TaskId) -> bool:
        """Delete task by ID"""
        try:
            response = self.table.delete_item(
                Key={
                    'PK': f'TASK#{task_id}',
                    'SK': f'TASK#{task_id}'
                },
                ReturnValues='ALL_OLD'
            )
            
            return 'Attributes' in response
            
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False
    
    async def exists(self, task_id: TaskId) -> bool:
        """Check if task exists"""
        task = await self.find_by_id(task_id)
        return task is not None
    
    def _map_to_entity(self, item: dict) -> Task:
        """Map DynamoDB item to Task entity"""
        return Task(
            id=TaskId(item['TaskId']),
            user_id=UserId(item['UserId']),
            title=item['Title'],
            description=item['Description'],
            status=TaskStatus(item['Status']),
            created_at=datetime.fromisoformat(item['CreatedAt']),
            updated_at=datetime.fromisoformat(item['UpdatedAt']) if item.get('UpdatedAt') else None,
            completed_at=datetime.fromisoformat(item['CompletedAt']) if item.get('CompletedAt') else None
        )
```

### Step 10: Create Event Bus Implementation

```python
# src/infrastructure/messaging/sns_event_bus.py
import boto3
import json
from typing import List
from src.domain.events import DomainEvent

class SNSEventBus:
    """SNS implementation of event bus"""
    
    def __init__(self, topic_arn: str):
        self.sns_client = boto3.client('sns')
        self.topic_arn = topic_arn
    
    async def publish(self, events: List[DomainEvent]) -> None:
        """Publish domain events to SNS topic"""
        for event in events:
            try:
                message = {
                    'event_type': event.__class__.__name__,
                    'event_id': event.event_id,
                    'aggregate_id': event.aggregate_id,
                    'timestamp': event.timestamp.isoformat(),
                    'data': event.to_dict()
                }
                
                self.sns_client.publish(
                    TopicArn=self.topic_arn,
                    Subject=f'Domain Event: {event.__class__.__name__}',
                    Message=json.dumps(message),
                    MessageAttributes={
                        'event_type': {
                            'DataType': 'String',
                            'StringValue': event.__class__.__name__
                        }
                    }
                )
                
                print(f"Published event: {event.__class__.__name__}")
                
            except Exception as e:
                print(f"Error publishing event {event.__class__.__name__}: {e}")
                raise
```

### Step 11: Create Dependency Injection Container

```python
# src/infrastructure/container.py
import os
from dependency_injector import containers, providers
from src.domain.repositories import TaskRepository
from src.infrastructure.repositories import DynamoDBTaskRepository
from src.infrastructure.messaging import SNSEventBus
from src.application.services import (
    CreateTaskService,
    GetTaskService,
    ListTasksService,
    CompleteTaskService
)

class Container(containers.DeclarativeContainer):
    """Dependency injection container"""
    
    # Configuration
    config = providers.Configuration()
    
    # Infrastructure
    task_repository = providers.Singleton(
        DynamoDBTaskRepository,
        table_name=config.table_name
    )
    
    event_bus = providers.Singleton(
        SNSEventBus,
        topic_arn=config.topic_arn
    )
    
    # Services
    create_task = providers.Factory(
        CreateTaskService,
        task_repository=task_repository,
        event_bus=event_bus
    )
    
    get_task = providers.Factory(
        GetTaskService,
        task_repository=task_repository
    )
    
    list_tasks = providers.Factory(
        ListTasksService,
        task_repository=task_repository
    )
    
    complete_task = providers.Factory(
        CompleteTaskService,
        task_repository=task_repository,
        event_bus=event_bus
    )

def create_container() -> Container:
    """Create and configure the container"""
    container = Container()
    
    # Load configuration from environment variables
    container.config.table_name.from_env("TABLE_NAME", required=True)
    container.config.topic_arn.from_env("TOPIC_ARN", required=True)
    
    return container
```

---

## 🔗 API Adapter Layer Implementation

> **The adapter layer exposes our services as REST API endpoints.**

### Step 12: Create API Response Helpers

```python
# src/commons/utils/api_response.py
import json
from typing import Any, Dict, Optional

class APIResponse:
    """Helper class for creating consistent API responses"""
    
    @staticmethod
    def success(data: Any = None, status_code: int = 200) -> Dict[str, Any]:
        """Create a successful API response"""
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'data': data
            })
        }
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Create an error API response"""
        error_data = {
            'success': False,
            'error': {
                'message': message
            }
        }
        
        if error_code:
            error_data['error']['code'] = error_code
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(error_data)
        }
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> Dict[str, Any]:
        """Create a 404 not found response"""
        return APIResponse.error(message, 404, "NOT_FOUND")
    
    @staticmethod
    def validation_error(message: str) -> Dict[str, Any]:
        """Create a validation error response"""
        return APIResponse.error(message, 400, "VALIDATION_ERROR")
    
    @staticmethod
    def internal_error(message: str = "Internal server error") -> Dict[str, Any]:
        """Create a 500 internal server error response"""
        return APIResponse.error(message, 500, "INTERNAL_ERROR")
```

### Step 13: Create Lambda Handlers

```python
# src/adapters/api/create_task.py
import json
import traceback
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from dependency_injector.wiring import Provide, inject
from src.infrastructure.container import Container, create_container
from src.application.services import CreateTaskService
from src.commons.utils import APIResponse

# Initialize observability tools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize container
container = create_container()
container.wire(modules=[__name__])

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
@inject
def lambda_handler(
    event: Dict[str, Any],
    context: Any,
    service: CreateTaskService = Provide[Container.create_task]
) -> Dict[str, Any]:
    """Lambda handler for creating a task"""
    
    try:
        # Add metrics
        metrics.add_metric(name="CreateTaskRequests", unit=MetricUnit.Count, value=1)
        
        # Parse request body
        try:
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', {})
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return APIResponse.validation_error("Invalid JSON in request body")
        
        # Extract required fields
        user_id = body.get('user_id')
        title = body.get('title')
        description = body.get('description', '')
        
        # Validate required fields
        if not user_id:
            return APIResponse.validation_error("user_id is required")
        
        if not title:
            return APIResponse.validation_error("title is required")
        
        # Execute service
        result = await service.execute(user_id, title, description)
        
        logger.info(f"Task created successfully: {result['task_id']}")
        metrics.add_metric(name="TasksCreated", unit=MetricUnit.Count, value=1)
        
        return APIResponse.success(result, 201)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return APIResponse.validation_error(str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        metrics.add_metric(name="CreateTaskErrors", unit=MetricUnit.Count, value=1)
        return APIResponse.internal_error()
```

```python
# src/adapters/api/get_task.py
import traceback
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from dependency_injector.wiring import Provide, inject
from src.infrastructure.container import Container, create_container
from src.application.services import GetTaskService
from src.commons.utils import APIResponse

logger = Logger()
tracer = Tracer()
metrics = Metrics()

container = create_container()
container.wire(modules=[__name__])

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
@inject
def lambda_handler(
    event: Dict[str, Any],
    context: Any,
    service: GetTaskService = Provide[Container.get_task]
) -> Dict[str, Any]:
    """Lambda handler for getting a task by ID"""
    
    try:
        metrics.add_metric(name="GetTaskRequests", unit=MetricUnit.Count, value=1)
        
        # Extract task ID from path parameters
        task_id = event.get('pathParameters', {}).get('task_id')
        
        if not task_id:
            return APIResponse.validation_error("task_id is required")
        
        # Execute service
        result = await service.execute(task_id)
        
        if result is None:
            logger.info(f"Task not found: {task_id}")
            return APIResponse.not_found("Task not found")
        
        logger.info(f"Task retrieved successfully: {task_id}")
        metrics.add_metric(name="TasksRetrieved", unit=MetricUnit.Count, value=1)
        
        return APIResponse.success(result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return APIResponse.validation_error(str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        metrics.add_metric(name="GetTaskErrors", unit=MetricUnit.Count, value=1)
        return APIResponse.internal_error()
```

```python
# src/adapters/api/list_tasks.py
import traceback
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from dependency_injector.wiring import Provide, inject
from src.infrastructure.container import Container, create_container
from src.application.services import ListTasksService
from src.commons.utils import APIResponse

logger = Logger()
tracer = Tracer()
metrics = Metrics()

container = create_container()
container.wire(modules=[__name__])

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
@inject
def lambda_handler(
    event: Dict[str, Any],
    context: Any,
    service: ListTasksService = Provide[Container.list_tasks]
) -> Dict[str, Any]:
    """Lambda handler for listing tasks by user ID"""
    
    try:
        metrics.add_metric(name="ListTasksRequests", unit=MetricUnit.Count, value=1)
        
        # Extract user ID from query parameters
        user_id = event.get('queryStringParameters', {}).get('user_id') if event.get('queryStringParameters') else None
        
        if not user_id:
            return APIResponse.validation_error("user_id query parameter is required")
        
        # Execute service
        result = await service.execute(user_id)
        
        logger.info(f"Listed {len(result)} tasks for user: {user_id}")
        metrics.add_metric(name="TasksListed", unit=MetricUnit.Count, value=len(result))
        
        return APIResponse.success(result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return APIResponse.validation_error(str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        metrics.add_metric(name="ListTasksErrors", unit=MetricUnit.Count, value=1)
        return APIResponse.internal_error()
```

```python
# src/adapters/api/complete_task.py
import traceback
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from dependency_injector.wiring import Provide, inject
from src.infrastructure.container import Container, create_container
from src.application.services import CompleteTaskService
from src.commons.utils import APIResponse

logger = Logger()
tracer = Tracer()
metrics = Metrics()

container = create_container()
container.wire(modules=[__name__])

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
@inject
def lambda_handler(
    event: Dict[str, Any],
    context: Any,
    service: CompleteTaskService = Provide[Container.complete_task]
) -> Dict[str, Any]:
    """Lambda handler for completing a task"""
    
    try:
        metrics.add_metric(name="CompleteTaskRequests", unit=MetricUnit.Count, value=1)
        
        # Extract task ID from path parameters
        task_id = event.get('pathParameters', {}).get('task_id')
        
        if not task_id:
            return APIResponse.validation_error("task_id is required")
        
        # Execute service
        result = await service.execute(task_id)
        
        if result is None:
            logger.info(f"Task not found: {task_id}")
            return APIResponse.not_found("Task not found")
        
        logger.info(f"Task completed successfully: {task_id}")
        metrics.add_metric(name="TasksCompleted", unit=MetricUnit.Count, value=1)
        
        return APIResponse.success(result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return APIResponse.validation_error(str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        metrics.add_metric(name="CompleteTaskErrors", unit=MetricUnit.Count, value=1)
        return APIResponse.internal_error()
```

### Step 14: Create Event Processing Handler

```python
# src/adapters/events/process_events.py
import json
import traceback
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process task events from SQS"""
    
    failed_records = []
    
    try:
        metrics.add_metric(name="EventProcessingRequests", unit=MetricUnit.Count, value=1)
        
        for record in event['Records']:
            try:
                # Parse SNS message from SQS
                sns_message = json.loads(record['body'])
                message_data = json.loads(sns_message['Message'])
                
                event_type = message_data.get('event_type')
                logger.info(f"Processing event: {event_type}")
                
                # Process different event types
                if event_type == 'TaskCompleted':
                    await process_task_completed(message_data)
                elif event_type == 'TaskCreated':
                    await process_task_created(message_data)
                else:
                    logger.info(f"Unknown event type: {event_type}")
                
                metrics.add_metric(name="EventsProcessed", unit=MetricUnit.Count, value=1)
                
            except Exception as e:
                logger.error(f"Failed to process record: {str(e)}")
                logger.error(traceback.format_exc())
                failed_records.append({
                    'itemIdentifier': record['messageId']
                })
                metrics.add_metric(name="EventProcessingErrors", unit=MetricUnit.Count, value=1)
        
        # Return failed records for SQS partial batch failure handling
        return {
            'batchItemFailures': failed_records
        }
        
    except Exception as e:
        logger.error(f"Critical error in event processing: {str(e)}")
        logger.error(traceback.format_exc())
        metrics.add_metric(name="CriticalEventProcessingErrors", unit=MetricUnit.Count, value=1)
        raise

async def process_task_completed(event_data: Dict[str, Any]) -> None:
    """Process TaskCompleted event"""
    data = event_data.get('data', {})
    task_title = data.get('task_title')
    user_id = data.get('user_id')
    
    logger.info(f"Task completed: {task_title} by user {user_id}")
    
    # Here you could:
    # - Send email notification
    # - Update user statistics
    # - Trigger other workflows

async def process_task_created(event_data: Dict[str, Any]) -> None:
    """Process TaskCreated event"""
    data = event_data.get('data', {})
    task_title = data.get('task_title')
    user_id = data.get('user_id')
    
    logger.info(f"New task created: {task_title} by user {user_id}")
    
    # Here you could:
    # - Send welcome email
    # - Update user onboarding progress
    # - Analytics tracking
```

---

## 🏗️ CDK Infrastructure Implementation

> **Deploy your infrastructure using AWS CDK with Python.**

### Step 15: Initialize CDK Project

```bash
# Create CDK directory and initialize
cd infrastructure
mkdir cdk && cd cdk

# Initialize CDK with Python
cdk init app --language python

# Activate virtual environment and install dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Install additional dependencies
pip install aws-cdk.aws-apigateway aws-cdk.aws-lambda-python-alpha
```

### Step 16: Create CDK Stack

```python
# infrastructure/cdk/backend_tutorial/backend_tutorial_stack.py
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_sns_subscriptions as sqs_subscriptions,
    aws_lambda_event_sources as lambda_event_sources,
    Duration,
    CfnOutput,
    RemovalPolicy
)
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct

class BackendTutorialStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table
        tasks_table = dynamodb.Table(
            self, "TasksTable",
            table_name=f"{environment}-tasks",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Use RETAIN for production
            point_in_time_recovery=True,
        )

        # Global Secondary Index for user queries
        tasks_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(name="GSI1PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="GSI1SK", type=dynamodb.AttributeType.STRING),
        )

        # SNS Topic for events
        events_topic = sns.Topic(
            self, "TaskEventsTopic",
            topic_name=f"{environment}-task-events",
        )

        # SQS Queue for event processing
        events_queue = sqs.Queue(
            self, "TaskEventsQueue",
            queue_name=f"{environment}-task-events",
            visibility_timeout=Duration.minutes(5),
            dead_letter_queue=sqs.DeadLetterQueue(
                queue=sqs.Queue(
                    self, "TaskEventsQueueDLQ",
                    queue_name=f"{environment}-task-events-dlq",
                ),
                max_receive_count=3,
            ),
        )

        # Subscribe queue to topic
        events_topic.add_subscription(sqs_subscriptions.SqsSubscription(events_queue))

        # Common Lambda environment variables
        common_environment = {
            "TABLE_NAME": tasks_table.table_name,
            "TOPIC_ARN": events_topic.topic_arn,
            "POWERTOOLS_SERVICE_NAME": "TaskAPI",
            "POWERTOOLS_LOG_LEVEL": "INFO",
            "ENVIRONMENT": environment,
        }

        # Lambda function configuration
        lambda_props = {
            "runtime": lambda_.Runtime.PYTHON_3_12,
            "timeout": Duration.seconds(30),
            "memory_size": 512,
            "environment": common_environment,
            "entry": "../../src",  # Path to source code
        }

        # API Lambda Functions
        create_task_function = PythonFunction(
            self, "CreateTaskFunction",
            function_name=f"{environment}-create-task",
            handler="lambda_handler",
            index="adapters/api/create_task.py",
            **lambda_props
        )

        get_task_function = PythonFunction(
            self, "GetTaskFunction",
            function_name=f"{environment}-get-task",
            handler="lambda_handler",
            index="adapters/api/get_task.py",
            **lambda_props
        )

        list_tasks_function = PythonFunction(
            self, "ListTasksFunction",
            function_name=f"{environment}-list-tasks",
            handler="lambda_handler",
            index="adapters/api/list_tasks.py",
            **lambda_props
        )

        complete_task_function = PythonFunction(
            self, "CompleteTaskFunction",
            function_name=f"{environment}-complete-task",
            handler="lambda_handler",
            index="adapters/api/complete_task.py",
            **lambda_props
        )

        # Grant permissions to Lambda functions
        lambda_functions = [create_task_function, get_task_function, list_tasks_function, complete_task_function]
        
        for fn in lambda_functions:
            # DynamoDB permissions
            tasks_table.grant_read_write_data(fn)
            # SNS permissions
            events_topic.grant_publish(fn)

        # API Gateway with Swagger documentation
        api = apigateway.RestApi(
            self, "TaskAPI",
            rest_api_name=f"{environment}-task-api",
            description="Task Management API with Swagger documentation",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"],
            ),
        )

        # Create API model for request validation
        task_model = api.add_model(
            "TaskModel",
            content_type="application/json",
            schema=apigateway.JsonSchema(
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    "user_id": apigateway.JsonSchema(type=apigateway.JsonSchemaType.STRING, min_length=1),
                    "title": apigateway.JsonSchema(type=apigateway.JsonSchemaType.STRING, min_length=1, max_length=200),
                    "description": apigateway.JsonSchema(type=apigateway.JsonSchemaType.STRING, max_length=1000)
                },
                required=["user_id", "title"]
            )
        )

        # Request validator
        request_validator = api.add_request_validator(
            "TaskRequestValidator",
            validate_request_body=True,
        )

        # API Resources and Methods
        tasks_resource = api.root.add_resource("tasks")
        
        # POST /tasks - Create task
        tasks_resource.add_method(
            "POST", 
            apigateway.LambdaIntegration(create_task_function),
            request_validator=request_validator,
            request_models={"application/json": task_model}
        )

        # GET /tasks?user_id=xxx - List tasks
        tasks_resource.add_method("GET", apigateway.LambdaIntegration(list_tasks_function))

        # GET /tasks/{task_id} - Get task
        task_resource = tasks_resource.add_resource("{task_id}")
        task_resource.add_method("GET", apigateway.LambdaIntegration(get_task_function))

        # POST /tasks/{task_id}/complete - Complete task
        complete_resource = task_resource.add_resource("complete")
        complete_resource.add_method("POST", apigateway.LambdaIntegration(complete_task_function))

        # Event Processing Lambda
        process_events_function = PythonFunction(
            self, "ProcessEventsFunction",
            function_name=f"{environment}-process-events",
            handler="lambda_handler",
            index="adapters/events/process_events.py",
            **lambda_props
        )

        # Grant permissions to event processing function
        tasks_table.grant_read_data(process_events_function)
        
        # Add SQS event source
        process_events_function.add_event_source(
            lambda_event_sources.SqsEventSource(
                events_queue,
                batch_size=10,
                report_batch_item_failures=True,
            )
        )

        # Outputs
        CfnOutput(
            self, "ApiUrl",
            value=api.url,
            description="Task API URL",
            export_name=f"{environment}-task-api-url",
        )

        CfnOutput(
            self, "ApiDocumentationUrl",
            value=f"{api.url}swagger",
            description="API Documentation URL",
            export_name=f"{environment}-task-api-docs-url",
        )

        CfnOutput(
            self, "TableName",
            value=tasks_table.table_name,
            description="DynamoDB Table Name",
            export_name=f"{environment}-tasks-table-name",
        )

        CfnOutput(
            self, "TopicArn",
            value=events_topic.topic_arn,
            description="SNS Topic ARN",
            export_name=f"{environment}-events-topic-arn",
        )
```

### Step 17: Create Swagger Documentation

```python
# docs/swagger_spec.py
"""
OpenAPI/Swagger specification for the Task Management API
"""

def get_swagger_spec(api_url: str) -> dict:
    """Generate Swagger specification for the API"""
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "Task Management API",
            "description": "A simple task management API built with serverless architecture",
            "version": "1.0.0",
            "contact": {
                "name": "Backend Tutorial",
                "url": "https://github.com/your-org/backend-tutorial"
            }
        },
        "servers": [
            {
                "url": api_url,
                "description": "Task Management API"
            }
        ],
        "paths": {
            "/tasks": {
                "post": {
                    "summary": "Create a new task",
                    "description": "Creates a new task for a user",
                    "tags": ["Tasks"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateTaskRequest"},
                                "example": {
                                    "user_id": "user-123",
                                    "title": "Complete project documentation",
                                    "description": "Write comprehensive documentation for the backend tutorial project"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Task created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TaskResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                },
                "get": {
                    "summary": "List tasks for a user",
                    "description": "Retrieves all tasks for a specific user",
                    "tags": ["Tasks"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "User ID to filter tasks",
                            "example": "user-123"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of tasks",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "data": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Task"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tasks/{task_id}": {
                "get": {
                    "summary": "Get a specific task",
                    "description": "Retrieves a task by its ID",
                    "tags": ["Tasks"],
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Task ID",
                            "example": "task-123e4567-e89b-12d3-a456-426614174000"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Task found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TaskResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Task not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/tasks/{task_id}/complete": {
                "post": {
                    "summary": "Complete a task",
                    "description": "Marks a task as completed",
                    "tags": ["Tasks"],
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Task ID",
                            "example": "task-123e4567-e89b-12d3-a456-426614174000"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Task completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TaskResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Task not found"
                        },
                        "400": {
                            "description": "Task cannot be completed (invalid status)"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "CreateTaskRequest": {
                    "type": "object",
                    "required": ["user_id", "title"],
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the user creating the task",
                            "minLength": 1
                        },
                        "title": {
                            "type": "string",
                            "description": "Task title",
                            "minLength": 1,
                            "maxLength": 200
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description",
                            "maxLength": 1000
                        }
                    }
                },
                "Task": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Unique task identifier"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User who owns the task"
                        },
                        "title": {
                            "type": "string",
                            "description": "Task title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "cancelled"],
                            "description": "Current task status"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Task creation timestamp"
                        },
                        "updated_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Task last update timestamp",
                            "nullable": True
                        },
                        "completed_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Task completion timestamp",
                            "nullable": True
                        }
                    }
                },
                "TaskResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "example": True
                        },
                        "data": {
                            "$ref": "#/components/schemas/Task"
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "example": False
                        },
                        "error": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Error message"
                                },
                                "code": {
                                    "type": "string",
                                    "description": "Error code"
                                }
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "Tasks",
                "description": "Task management operations"
            }
        ]
    }
```

### Step 18: Add Swagger Integration to API Gateway

```python
# Add to infrastructure/cdk/backend_tutorial/backend_tutorial_stack.py (after API Gateway creation)

        # Add Swagger documentation endpoint
        swagger_integration = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": "'application/json'"
                    },
                    response_templates={
                        "application/json": json.dumps(get_swagger_spec(api.url))
                    }
                )
            ],
            request_templates={
                "application/json": '{"statusCode": 200}'
            }
        )

        # Add swagger endpoint
        swagger_resource = api.root.add_resource("swagger")
        swagger_resource.add_method(
            "GET",
            swagger_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    }
                )
            ]
        )
```

### Step 19: Update CDK App Configuration

```python
# infrastructure/cdk/app.py
#!/usr/bin/env python3
import aws_cdk as cdk
from backend_tutorial.backend_tutorial_stack import BackendTutorialStack

app = cdk.App()

# Staging environment
BackendTutorialStack(
    app, "BackendTutorialStagingStack",
    environment="staging",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1",
    ),
    tags={
        "Environment": "staging",
        "Project": "backend-tutorial",
    }
)

app.synth()
```

---

## 🧪 Testing Implementation

> **Comprehensive testing ensures reliability and maintainability.**

### Step 20: Configure Testing Environment

```python
# tests/conftest.py
import pytest
import os
import asyncio
from moto import mock_aws
from dependency_injector import containers, providers
from src.infrastructure.container import Container

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture(scope="function")
def dynamodb_table(aws_credentials):
    """Create mocked DynamoDB table."""
    with mock_aws():
        import boto3
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        table = dynamodb.create_table(
            TableName="test-tasks",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "BillingMode": "PAY_PER_REQUEST"
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        
        yield table

@pytest.fixture(scope="function")
def test_container(dynamodb_table):
    """Create test dependency injection container."""
    container = Container()
    container.config.table_name.from_value("test-tasks")
    container.config.topic_arn.from_value("arn:aws:sns:us-east-1:123456789012:test-topic")
    return container
```

### Step 21: Create Unit Tests

```python
# tests/unit/test_task_entity.py
import pytest
from datetime import datetime, timezone
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus
from src.domain.events import TaskCreated, TaskCompleted

class TestTask:
    def test_task_creation_generates_event(self):
        """Test that creating a task generates TaskCreated event"""
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        events = task.pop_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCreated)
        assert events[0].task_title == "Test Task"
        assert events[0].user_id == "user-456"
    
    def test_task_completion_generates_events(self):
        """Test that completing a task generates appropriate events"""
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Clear creation event
        task.pop_events()
        
        # Complete the task
        task.update_status(TaskStatus.COMPLETED)
        
        events = task.pop_events()
        assert len(events) == 2  # StatusChanged + TaskCompleted
        
        # Find the TaskCompleted event
        completed_events = [e for e in events if isinstance(e, TaskCompleted)]
        assert len(completed_events) == 1
        assert completed_events[0].task_title == "Test Task"
    
    def test_task_validation(self):
        """Test task validation rules"""
        # Empty title should raise error
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id=TaskId("task-123"),
                user_id=UserId("user-456"),
                title="",
                description="Test",
                status=TaskStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
        
        # Long title should raise error
        with pytest.raises(ValueError, match="Task title cannot exceed 200 characters"):
            Task(
                id=TaskId("task-123"),
                user_id=UserId("user-456"),
                title="x" * 201,
                description="Test",
                status=TaskStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
```

### Step 22: Create Integration Tests

```python
# tests/integration/test_dynamodb_repository.py
import pytest
from datetime import datetime, timezone
from src.infrastructure.repositories import DynamoDBTaskRepository
from src.domain.entities import Task
from src.domain.value_objects import TaskId, UserId, TaskStatus

@pytest.mark.asyncio
class TestDynamoDBTaskRepository:
    async def test_save_and_find_task(self, dynamodb_table):
        """Test saving and finding a task"""
        repository = DynamoDBTaskRepository("test-tasks")
        
        # Create a task
        task = Task(
            id=TaskId("task-123"),
            user_id=UserId("user-456"),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        # Save task
        await repository.save(task)
        
        # Find task
        found_task = await repository.find_by_id(TaskId("task-123"))
        
        assert found_task is not None
        assert found_task.id == task.id
        assert found_task.title == task.title
        assert found_task.user_id == task.user_id
        assert found_task.status == task.status
    
    async def test_find_by_user_id(self, dynamodb_table):
        """Test finding tasks by user ID"""
        repository = DynamoDBTaskRepository("test-tasks")
        user_id = UserId("user-456")
        
        # Create multiple tasks for the same user
        tasks = []
        for i in range(3):
            task = Task(
                id=TaskId(f"task-{i}"),
                user_id=user_id,
                title=f"Task {i}",
                description=f"Description {i}",
                status=TaskStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
            tasks.append(task)
            await repository.save(task)
        
        # Find tasks by user ID
        found_tasks = await repository.find_by_user_id(user_id)
        
        assert len(found_tasks) == 3
        assert all(t.user_id == user_id for t in found_tasks)
```

### Step 23: Create API Tests

```python
# tests/integration/test_api_handlers.py
import pytest
import json
from unittest.mock import AsyncMock, patch
from src.adapters.api.create_task import lambda_handler as create_handler
from src.adapters.api.get_task import lambda_handler as get_handler

@pytest.mark.asyncio
class TestAPIHandlers:
    @patch('src.adapters.api.create_task.create_container')
    async def test_create_task_success(self, mock_container):
        """Test successful task creation via API"""
        # Mock service
        mock_service = AsyncMock()
        mock_service.execute.return_value = {
            "task_id": "task-123",
            "title": "Test Task",
            "status": "pending",
            "user_id": "user-456"
        }
        
        mock_container.return_value.create_task.return_value = mock_service
        
        # Create test event
        event = {
            "body": json.dumps({
                "user_id": "user-456",
                "title": "Test Task",
                "description": "Test Description"
            })
        }
        
        # Execute handler
        response = await create_handler(event, {})
        
        # Verify response
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["task_id"] == "task-123"
```

---

## 🚀 Deployment and Testing

> **Deploy your application to AWS and verify everything works.**

### Step 24: Configure Project Dependencies

```toml
# pyproject.toml (update the complete file)
[tool.poetry]
name = "backend-tutorial"
version = "0.1.0"
description = "Serverless Python backend tutorial with DDD and CLEAN architecture"
authors = ["Your Organization <team@company.com>"]
packages = [{include = "src"}]

[tool.poetry.dependencies]
python = "^3.12"
boto3 = "^1.34.0"
pydantic = "^2.5.0"
dependency-injector = "^4.41.0"
aws-lambda-powertools = "^2.30.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
moto = "^4.2.0"
black = "^23.12.0"
isort = "^5.13.0"
mypy = "^1.8.0"
pre-commit = "^3.6.0"
aws-cdk-lib = "^2.100.0"
constructs = "^10.3.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.12"
packages = ["src"]
strict = true
warn_return_any = true
warn_unused_configs = true
check_untyped_defs = true

[tool.black]
line-length = 100
target-version = ["py312"]
include = '\.pyi?
                            "

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
```

### Step 25: Run Tests

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest -v

# Run linting
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run mypy src/
```

**✅ Verification:** All tests should pass before deployment.

### Step 26: Deploy with CDK

```bash
# Navigate to CDK directory
cd infrastructure/cdk

# Install CDK dependencies
pip install -r requirements.txt

# Bootstrap CDK (only needed once per account/region)
cdk bootstrap

# Synthesize CloudFormation template
cdk synth BackendTutorialStagingStack

# Deploy to staging
cdk deploy BackendTutorialStagingStack
```

**✅ Verification:** 
- CDK deployment should complete successfully
- Note the API URL and documentation URL from outputs
- Check AWS Console to verify resources were created

### Step 27: Test the Deployed API

```python
# scripts/test_deployed_api.py
import requests
import json
import sys

def test_api(base_url):
    """Test the deployed API"""
    
    print(f"🚀 Testing API at: {base_url}")
    base_url = base_url.rstrip('/')
    
    # Test 1: Create a task
    print("\n1️⃣ Creating a task...")
    create_data = {
        "user_id": "test-user-123",
        "title": "My First Task",
        "description": "This is a test task created via API"
    }
    
    response = requests.post(
        f"{base_url}/tasks",
        json=create_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        task_data = response.json()
        print(f"✅ Task created successfully!")
        print(f"   Task ID: {task_data['data']['task_id']}")
        print(f"   Title: {task_data['data']['title']}")
        
        task_id = task_data['data']['task_id']
        
        # Test 2: Get the task
        print(f"\n2️⃣ Getting task {task_id}...")
        response = requests.get(f"{base_url}/tasks/{task_id}")
        
        if response.status_code == 200:
            task_data = response.json()
            print(f"✅ Task retrieved successfully!")
            print(f"   Status: {task_data['data']['status']}")
        else:
            print(f"❌ Failed to get task: {response.status_code}")
            return False
        
        # Test 3: List tasks
        print(f"\n3️⃣ Listing tasks for user...")
        response = requests.get(f"{base_url}/tasks?user_id=test-user-123")
        
        if response.status_code == 200:
            tasks_data = response.json()
            print(f"✅ Listed {len(tasks_data['data'])} tasks!")
        else:
            print(f"❌ Failed to list tasks: {response.status_code}")
            return False
        
        # Test 4: Complete the task
        print(f"\n4️⃣ Completing task {task_id}...")
        response = requests.post(f"{base_url}/tasks/{task_id}/complete")
        
        if response.status_code == 200:
            task_data = response.json()
            print(f"✅ Task completed successfully!")
            print(f"   Status: {task_data['data']['status']}")
            print(f"   Completed at: {task_data['data']['completed_at']}")
        else:
            print(f"❌ Failed to complete task: {response.status_code}")
            return False
        
        # Test 5: Test 404 for non-existent task
        print(f"\n5️⃣ Testing 404 for non-existent task...")
        response = requests.get(f"{base_url}/tasks/non-existent-task")
        
        if response.status_code == 404:
            print(f"✅ 404 handling works correctly!")
        else:
            print(f"❌ Expected 404, got: {response.status_code}")
            return False
        
        print(f"\n🎉 All API tests passed!")
        print(f"📚 View API documentation at: {base_url}/swagger")
        return True
        
    else:
        print(f"❌ Failed to create task: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_deployed_api.py <API_URL>")
        print("Example: python test_deployed_api.py https://abc123.execute-api.us-east-1.amazonaws.com/prod/")
        sys.exit(1)
    
    api_url = sys.argv[1]
    success = test_api(api_url)
    sys.exit(0 if success else 1)
```

**Run the test:**
```bash
# Get API URL from CDK output and test
poetry run python scripts/test_deployed_api.py https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/
```

---

## 🛡️ Production Readiness

> **Essential configurations for production deployment.**

### Step 28: Environment Configuration

```python
# src/commons/config/settings.py
import os
from enum import Enum
from typing import Optional

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings:
    def __init__(self):
        self.environment = Environment(os.getenv("ENVIRONMENT", "development"))
        self.table_name = os.getenv("TABLE_NAME")
        self.topic_arn = os.getenv("TOPIC_ARN")
        self.log_level = os.getenv("POWERTOOLS_LOG_LEVEL", "INFO")
        
        # Validation
        if not self.table_name:
            raise ValueError("TABLE_NAME environment variable is required")
        if not self.topic_arn:
            raise ValueError("TOPIC_ARN environment variable is required")
    
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

# Global settings instance
settings = Settings()
```

### Step 29: Monitoring and Alerts

```python
# Add to CDK stack for production monitoring
        import aws_cdk.aws_cloudwatch as cloudwatch
        import aws_cdk.aws_sns as sns
        
        # Create SNS topic for alerts
        alerts_topic = sns.Topic(
            self, "AlertsTopic",
            topic_name=f"{environment}-api-alerts",
        )
        
        # Lambda error rate alarm
        cloudwatch.Alarm(
            self, "LambdaErrorAlarm",
            metric=create_task_function.metric_errors(),
            threshold=5,
            evaluation_periods=2,
            alarm_description="Lambda function error rate is too high",
        )
        
        # API Gateway 5xx errors
        cloudwatch.Alarm(
            self, "ApiGateway5xxAlarm",
            metric=api.metric_server_error(),
            threshold=10,
            evaluation_periods=2,
            alarm_description="API Gateway 5xx error rate is too high",
        )
        
        # DynamoDB throttling
        cloudwatch.Alarm(
            self, "DynamoDBThrottleAlarm",
            metric=tasks_table.metric_throttles(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="DynamoDB requests are being throttled",
        )
```

### Step 30: Security Enhancements

```python
# Add API key requirement and rate limiting to CDK stack
        # Create API key
        api_key = api.add_api_key("TaskApiKey")
        
        # Create usage plan
        usage_plan = api.add_usage_plan(
            "TaskApiUsagePlan",
            throttle={
                "rate_limit": 1000,  # requests per second
                "burst_limit": 2000  # burst capacity
            },
            quota={
                "limit": 10000,     # requests per day
                "period": apigateway.Period.DAY
            }
        )
        
        # Associate API key with usage plan
        usage_plan.add_api_key(api_key)
        usage_plan.add_api_stage(stage=api.deployment_stage)
```

---

## 📚 API Documentation

> **Your API includes interactive Swagger documentation.**

### Access Your API Documentation

Once deployed, your API documentation is available at:
```
https://your-api-id.execute-api.region.amazonaws.com/prod/swagger
```

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tasks` | Create a new task |
| `GET` | `/tasks?user_id={id}` | List tasks for a user |
| `GET` | `/tasks/{task_id}` | Get a specific task |
| `POST` | `/tasks/{task_id}/complete` | Complete a task |

### Example Usage

**Create a Task:**
```bash
curl -X POST https://your-api-url/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "title": "Complete project documentation",
    "description": "Write comprehensive docs"
  }'
```

**Get a Task:**
```bash
curl https://your-api-url/tasks/task-123e4567-e89b-12d3-a456-426614174000
```

**Complete a Task:**
```bash
curl -X POST https://your-api-url/tasks/task-123e4567-e89b-12d3-a456-426614174000/complete
```

---

## 🚀 Next Steps

### Immediate Extensions

1. **Add User Authentication**
   - Integrate AWS Cognito for user management
   - Add JWT token validation
   - Implement role-based access control

2. **Enhanced Task Features**
   - Add due dates and priorities
   - Implement task categories and tags
   - Add file attachments using S3

3. **Advanced Monitoring**
   - Set up X-Ray distributed tracing
   - Create CloudWatch dashboards
   - Implement custom metrics

### Architecture Improvements

1. **Caching Layer**
   - Add ElastiCache for frequently accessed data
   - Implement API response caching
   - Cache user sessions

2. **Database Optimization**
   - Implement proper DynamoDB access patterns
   - Add database connection pooling
   - Consider read replicas for heavy read workloads

3. **Event-Driven Enhancements**
   - Add email notifications via SES
   - Implement webhook callbacks
   - Create audit logging system

### DevOps and CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy Backend Tutorial

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Install dependencies
        run: poetry install
      - name: Run tests
        run: poetry run pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Deploy with CDK
        run: |
          cd infrastructure/cdk
          pip install -r requirements.txt
          cdk deploy BackendTutorialStagingStack --require-approval never
```

### Production Deployment

1. **Create Production Environment**
   ```python
   # Add to CDK app.py
   BackendTutorialStack(
       app, "BackendTutorialProdStack",
       environment="production",
       # Add production-specific configurations
   )
   ```

2. **Database Backup Strategy**
   - Enable DynamoDB point-in-time recovery
   - Set up automated backups
   - Implement disaster recovery procedures

3. **Security Hardening**
   - Enable AWS WAF for API protection
   - Implement API rate limiting
   - Add input validation and sanitization
   - Enable CloudTrail for audit logging

---

## 📋 Summary

**🎉 Congratulations!** You've successfully built a production-ready serverless Python backend that demonstrates:

### ✅ **Architecture Excellence**
- **Domain Driven Design** - Clean separation of business logic
- **CLEAN Architecture** - Maintainable and testable code structure  
- **SOLID Principles** - Proper dependency management and abstractions
- **Event-Driven Architecture** - Asynchronous processing with SNS/SQS

### ✅ **AWS Best Practices**
- **Infrastructure as Code** - Reproducible deployments with CDK
- **Serverless Architecture** - Auto-scaling with pay-per-use pricing
- **Production Monitoring** - CloudWatch logs, metrics, and alarms
- **API Documentation** - Interactive Swagger documentation

### ✅ **Development Best Practices**
- **Comprehensive Testing** - Unit, integration, and API tests
- **Type Safety** - Full type annotations with mypy
- **Code Quality** - Linting with black and isort
- **Dependency Management** - Poetry for reproducible builds

### 🎯 **Key Benefits**

1. **Maintainability**: Clear separation of concerns makes the codebase easy to understand and modify
2. **Testability**: Dependency injection and abstractions enable comprehensive testing
3. **Scalability**: Serverless architecture scales automatically with demand
4. **Cost-Effective**: Pay only for what you use
5. **Reliability**: Event-driven architecture with proper error handling and retries

### 🚀 **What You Can Build Next**

This tutorial provides a solid foundation for building:
- E-commerce order management systems
- Content management platforms
- IoT device data processing APIs
- Real-time analytics platforms
- Multi-tenant SaaS applications

The patterns and practices demonstrated here are used by major technology companies for production applications handling millions of requests.

**Remember:** Start simple, test thoroughly, and iterate based on real user feedback. The architecture supports growth from prototype to enterprise scale.

---

## 📚 Additional Resources

- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [AWS Lambda Powertools Documentation](https://docs.powertools.aws.dev/lambda/python/)
- [Domain-Driven Design Reference](https://domainlanguage.com/ddd/)
- [CLEAN Architecture Guide](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

**Happy coding! 🚀**
                            "