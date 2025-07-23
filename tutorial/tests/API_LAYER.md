# API Layer Testing Guide

> **Complete testing implementation for the API Layer following TDD principles.**

This guide shows you exactly what tests to write when implementing the API Layer from scratch, following Test-Driven Development (TDD) approach.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Lambda Handler Tests](#lambda-handler-tests)
- [API Gateway Integration Tests](#api-gateway-integration-tests)
- [Error Handling Tests](#error-handling-tests)
- [End-to-End API Tests](#end-to-end-api-tests)
- [Running API Tests](#running-api-tests)
- [TDD Workflow](#tdd-workflow)

---

## 🎯 Overview

The API Layer implements REST endpoints using AWS Lambda and API Gateway. We test it thoroughly to ensure:

- ✅ **HTTP handlers work correctly** - Request/response processing
- ✅ **Input validation is robust** - Invalid requests are handled gracefully
- ✅ **Business logic integration works** - Services are called correctly
- ✅ **Error responses are consistent** - Proper HTTP status codes and messages
- ✅ **Authentication and authorization work** - Security is enforced

## 🏗️ Test Structure

```
tests/
├── unit/api/                      # Unit tests (fast, isolated)
│   ├── test_create_task_handler.py # Create task endpoint tests
│   ├── test_get_task_handler.py   # Get task endpoint tests
│   ├── test_complete_task_handler.py # Complete task endpoint tests
│   ├── test_list_tasks_handler.py # List tasks endpoint tests
│   └── test_api_utils.py          # API utilities tests
├── integration/api/               # Integration tests (with services)
│   ├── test_api_integration.py    # API with real services
│   └── test_error_handling.py     # Error handling integration
└── e2e/api/                      # End-to-end tests (full API)
    ├── test_task_workflows.py     # Complete task workflows
    └── test_api_documentation.py  # API documentation tests
```

**Total API Tests:** 60+ tests (planned)

---

## 🌐 Lambda Handler Tests

### File: `tests/unit/api/test_create_task_handler.py`

Test the create task Lambda handler.

#### Test Categories:

1. **Request Processing Tests**
   - Test valid request processing
   - Test request body parsing
   - Test input validation

2. **Service Integration Tests**
   - Test service method calls
   - Test service error handling
   - Test dependency injection

3. **Response Formatting Tests**
   - Test successful response format
   - Test error response format
   - Test HTTP status codes

4. **Error Handling Tests**
   - Test malformed requests
   - Test missing fields
   - Test business logic errors

#### Example Test Implementation:

```python
@pytest.mark.api
@pytest.mark.unit
class TestCreateTaskHandler:
    @pytest.mark.asyncio
    async def test_create_task_with_valid_request(self, mock_container):
        """Test creating task with valid request"""
        # Setup mock service
        mock_service = AsyncMock()
        mock_service.execute.return_value = {
            "task_id": "task-123",
            "title": "Test Task",
            "description": "Test Description",
            "user_id": "user-456",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_container.return_value.create_task.return_value = mock_service
        
        # Create test event
        event = {
            "httpMethod": "POST",
            "path": "/tasks",
            "body": json.dumps({
                "user_id": "user-456",
                "title": "Test Task",
                "description": "Test Description"
            }),
            "headers": {"Content-Type": "application/json"}
        }
        
        # Execute handler
        from src.adapters.api.create_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify response
        assert response["statusCode"] == 201
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["task_id"] == "task-123"
        assert body["data"]["title"] == "Test Task"
        
        # Verify service was called
        mock_service.execute.assert_called_once_with(
            "user-456", "Test Task", "Test Description"
        )
    
    @pytest.mark.asyncio
    async def test_create_task_with_missing_title(self):
        """Test creating task with missing title"""
        event = {
            "httpMethod": "POST",
            "path": "/tasks",
            "body": json.dumps({
                "user_id": "user-456",
                "description": "Test Description"
                # Missing title
            }),
            "headers": {"Content-Type": "application/json"}
        }
        
        from src.adapters.api.create_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify error response
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "error" in body
        assert "title" in body["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_create_task_with_invalid_json(self):
        """Test creating task with invalid JSON"""
        event = {
            "httpMethod": "POST",
            "path": "/tasks",
            "body": "invalid json",
            "headers": {"Content-Type": "application/json"}
        }
        
        from src.adapters.api.create_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify error response
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "error" in body
        assert "json" in body["error"]["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_task_with_service_error(self, mock_container):
        """Test creating task when service raises error"""
        # Setup mock service to raise error
        mock_service = AsyncMock()
        mock_service.execute.side_effect = ValueError("Title cannot be empty")
        mock_container.return_value.create_task.return_value = mock_service
        
        event = {
            "httpMethod": "POST",
            "path": "/tasks",
            "body": json.dumps({
                "user_id": "user-456",
                "title": "",
                "description": "Test Description"
            }),
            "headers": {"Content-Type": "application/json"}
        }
        
        from src.adapters.api.create_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify error response
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["message"] == "Title cannot be empty"
```

### File: `tests/unit/api/test_get_task_handler.py`

Test the get task Lambda handler.

#### Example Test Implementation:

```python
@pytest.mark.api
@pytest.mark.unit
class TestGetTaskHandler:
    @pytest.mark.asyncio
    async def test_get_task_with_valid_id(self, mock_container):
        """Test getting task with valid ID"""
        # Setup mock service
        mock_service = AsyncMock()
        mock_service.execute.return_value = {
            "task_id": "task-123",
            "title": "Test Task",
            "description": "Test Description",
            "user_id": "user-456",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_container.return_value.get_task.return_value = mock_service
        
        # Create test event
        event = {
            "httpMethod": "GET",
            "path": "/tasks/task-123",
            "pathParameters": {"task_id": "task-123"}
        }
        
        # Execute handler
        from src.adapters.api.get_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify response
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["task_id"] == "task-123"
        
        # Verify service was called
        mock_service.execute.assert_called_once_with("task-123")
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_container):
        """Test getting task that doesn't exist"""
        # Setup mock service to return None
        mock_service = AsyncMock()
        mock_service.execute.return_value = None
        mock_container.return_value.get_task.return_value = mock_service
        
        event = {
            "httpMethod": "GET",
            "path": "/tasks/non-existent",
            "pathParameters": {"task_id": "non-existent"}
        }
        
        from src.adapters.api.get_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify 404 response
        assert response["statusCode"] == 404
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "not found" in body["error"]["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_task_with_missing_path_parameter(self):
        """Test getting task without task_id parameter"""
        event = {
            "httpMethod": "GET",
            "path": "/tasks/",
            "pathParameters": None
        }
        
        from src.adapters.api.get_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify error response
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "task_id" in body["error"]["message"]
```

### File: `tests/unit/api/test_list_tasks_handler.py`

Test the list tasks Lambda handler.

#### Example Test Implementation:

```python
@pytest.mark.api
@pytest.mark.unit
class TestListTasksHandler:
    @pytest.mark.asyncio
    async def test_list_tasks_with_valid_user_id(self, mock_container):
        """Test listing tasks with valid user ID"""
        # Setup mock service
        mock_service = AsyncMock()
        mock_service.execute.return_value = [
            {
                "task_id": "task-1",
                "title": "Task 1",
                "user_id": "user-456",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "task_id": "task-2",
                "title": "Task 2",
                "user_id": "user-456",
                "status": "completed",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        mock_container.return_value.list_tasks.return_value = mock_service
        
        # Create test event
        event = {
            "httpMethod": "GET",
            "path": "/tasks",
            "queryStringParameters": {"user_id": "user-456"}
        }
        
        # Execute handler
        from src.adapters.api.list_tasks import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify response
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert len(body["data"]) == 2
        assert body["data"][0]["task_id"] == "task-1"
        assert body["data"][1]["task_id"] == "task-2"
        
        # Verify service was called
        mock_service.execute.assert_called_once_with("user-456")
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_no_user_id(self):
        """Test listing tasks without user_id parameter"""
        event = {
            "httpMethod": "GET",
            "path": "/tasks",
            "queryStringParameters": None
        }
        
        from src.adapters.api.list_tasks import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify error response
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "user_id" in body["error"]["message"]
```

### File: `tests/unit/api/test_complete_task_handler.py`

Test the complete task Lambda handler.

#### Example Test Implementation:

```python
@pytest.mark.api
@pytest.mark.unit
class TestCompleteTaskHandler:
    @pytest.mark.asyncio
    async def test_complete_task_with_valid_id(self, mock_container):
        """Test completing task with valid ID"""
        # Setup mock service
        mock_service = AsyncMock()
        mock_service.execute.return_value = {
            "task_id": "task-123",
            "title": "Test Task",
            "user_id": "user-456",
            "status": "completed",
            "completed_at": "2024-01-01T12:00:00Z"
        }
        mock_container.return_value.complete_task.return_value = mock_service
        
        # Create test event
        event = {
            "httpMethod": "POST",
            "path": "/tasks/task-123/complete",
            "pathParameters": {"task_id": "task-123"}
        }
        
        # Execute handler
        from src.adapters.api.complete_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify response
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["status"] == "completed"
        assert "completed_at" in body["data"]
        
        # Verify service was called
        mock_service.execute.assert_called_once_with("task-123")
    
    @pytest.mark.asyncio
    async def test_complete_already_completed_task(self, mock_container):
        """Test completing task that is already completed"""
        # Setup mock service to raise error
        mock_service = AsyncMock()
        mock_service.execute.side_effect = ValueError("Task is already completed")
        mock_container.return_value.complete_task.return_value = mock_service
        
        event = {
            "httpMethod": "POST",
            "path": "/tasks/task-123/complete",
            "pathParameters": {"task_id": "task-123"}
        }
        
        from src.adapters.api.complete_task import lambda_handler
        response = await lambda_handler(event, {})
        
        # Verify error response
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "already completed" in body["error"]["message"]
```

---

## 🔧 API Utilities Tests

### File: `tests/unit/api/test_api_utils.py`

Test common API utilities and helpers.

#### Test Categories:

1. **Response Formatting Tests**
   - Test success response format
   - Test error response format
   - Test HTTP status code mapping

2. **Request Parsing Tests**
   - Test JSON body parsing
   - Test query parameter extraction
   - Test path parameter extraction

3. **Validation Tests**
   - Test input validation helpers
   - Test schema validation
   - Test error message formatting

#### Example Test Implementation:

```python
@pytest.mark.api
@pytest.mark.unit
class TestAPIUtils:
    def test_success_response_format(self):
        """Test success response formatting"""
        from src.adapters.api.utils import create_success_response
        
        data = {"task_id": "task-123", "title": "Test Task"}
        response = create_success_response(200, data)
        
        assert response["statusCode"] == 200
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"] == data
        assert "timestamp" in body
    
    def test_error_response_format(self):
        """Test error response formatting"""
        from src.adapters.api.utils import create_error_response
        
        response = create_error_response(400, "Invalid input", "VALIDATION_ERROR")
        
        assert response["statusCode"] == 400
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["message"] == "Invalid input"
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "timestamp" in body
    
    def test_parse_json_body_valid(self):
        """Test parsing valid JSON body"""
        from src.adapters.api.utils import parse_json_body
        
        event = {
            "body": json.dumps({"title": "Test Task", "user_id": "user-123"})
        }
        
        result = parse_json_body(event)
        assert result["title"] == "Test Task"
        assert result["user_id"] == "user-123"
    
    def test_parse_json_body_invalid(self):
        """Test parsing invalid JSON body"""
        from src.adapters.api.utils import parse_json_body
        
        event = {"body": "invalid json"}
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_json_body(event)
    
    def test_validate_required_fields(self):
        """Test required field validation"""
        from src.adapters.api.utils import validate_required_fields
        
        data = {"title": "Test Task", "user_id": "user-123"}
        required_fields = ["title", "user_id"]
        
        # Should not raise exception
        validate_required_fields(data, required_fields)
        
        # Should raise exception for missing field
        incomplete_data = {"title": "Test Task"}
        with pytest.raises(ValueError, match="user_id"):
            validate_required_fields(incomplete_data, required_fields)
```

---

## 🔗 Integration Tests

### File: `tests/integration/api/test_api_integration.py`

Test API handlers with real services.

#### Example Test Implementation:

```python
@pytest.mark.integration
@pytest.mark.asyncio
class TestAPIIntegration:
    async def test_create_and_get_task_flow(self, real_container):
        """Test complete create and get task flow"""
        # Create task
        create_event = {
            "httpMethod": "POST",
            "path": "/tasks",
            "body": json.dumps({
                "user_id": "user-456",
                "title": "Integration Test Task",
                "description": "Test Description"
            }),
            "headers": {"Content-Type": "application/json"}
        }
        
        from src.adapters.api.create_task import lambda_handler as create_handler
        create_response = await create_handler(create_event, {})
        
        assert create_response["statusCode"] == 201
        create_body = json.loads(create_response["body"])
        task_id = create_body["data"]["task_id"]
        
        # Get the created task
        get_event = {
            "httpMethod": "GET",
            "path": f"/tasks/{task_id}",
            "pathParameters": {"task_id": task_id}
        }
        
        from src.adapters.api.get_task import lambda_handler as get_handler
        get_response = await get_handler(get_event, {})
        
        assert get_response["statusCode"] == 200
        get_body = json.loads(get_response["body"])
        assert get_body["data"]["task_id"] == task_id
        assert get_body["data"]["title"] == "Integration Test Task"
    
    async def test_complete_task_flow(self, real_container):
        """Test complete task workflow"""
        # Create task first
        create_event = {
            "httpMethod": "POST",
            "path": "/tasks",
            "body": json.dumps({
                "user_id": "user-456",
                "title": "Task to Complete",
                "description": "Test Description"
            }),
            "headers": {"Content-Type": "application/json"}
        }
        
        from src.adapters.api.create_task import lambda_handler as create_handler
        create_response = await create_handler(create_event, {})
        
        task_id = json.loads(create_response["body"])["data"]["task_id"]
        
        # Complete the task
        complete_event = {
            "httpMethod": "POST",
            "path": f"/tasks/{task_id}/complete",
            "pathParameters": {"task_id": task_id}
        }
        
        from src.adapters.api.complete_task import lambda_handler as complete_handler
        complete_response = await complete_handler(complete_event, {})
        
        assert complete_response["statusCode"] == 200
        complete_body = json.loads(complete_response["body"])
        assert complete_body["data"]["status"] == "completed"
        assert "completed_at" in complete_body["data"]
```

---

## 🌐 End-to-End API Tests

### File: `tests/e2e/api/test_task_workflows.py`

Test complete task management workflows.

#### Example Test Implementation:

```python
@pytest.mark.e2e
@pytest.mark.asyncio
class TestTaskWorkflows:
    async def test_complete_task_management_workflow(self):
        """Test complete task management workflow"""
        user_id = "test-user-" + str(uuid.uuid4())
        
        # 1. Create multiple tasks
        tasks = []
        for i in range(3):
            create_event = {
                "httpMethod": "POST",
                "path": "/tasks",
                "body": json.dumps({
                    "user_id": user_id,
                    "title": f"Task {i+1}",
                    "description": f"Description {i+1}"
                }),
                "headers": {"Content-Type": "application/json"}
            }
            
            from src.adapters.api.create_task import lambda_handler as create_handler
            response = await create_handler(create_event, {})
            
            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            tasks.append(body["data"]["task_id"])
        
        # 2. List tasks for user
        list_event = {
            "httpMethod": "GET",
            "path": "/tasks",
            "queryStringParameters": {"user_id": user_id}
        }
        
        from src.adapters.api.list_tasks import lambda_handler as list_handler
        list_response = await list_handler(list_event, {})
        
        assert list_response["statusCode"] == 200
        list_body = json.loads(list_response["body"])
        assert len(list_body["data"]) == 3
        
        # 3. Complete one task
        complete_event = {
            "httpMethod": "POST",
            "path": f"/tasks/{tasks[0]}/complete",
            "pathParameters": {"task_id": tasks[0]}
        }
        
        from src.adapters.api.complete_task import lambda_handler as complete_handler
        complete_response = await complete_handler(complete_event, {})
        
        assert complete_response["statusCode"] == 200
        
        # 4. Verify task is completed
        get_event = {
            "httpMethod": "GET",
            "path": f"/tasks/{tasks[0]}",
            "pathParameters": {"task_id": tasks[0]}
        }
        
        from src.adapters.api.get_task import lambda_handler as get_handler
        get_response = await get_handler(get_event, {})
        
        assert get_response["statusCode"] == 200
        get_body = json.loads(get_response["body"])
        assert get_body["data"]["status"] == "completed"
```

---

## 🚀 Running API Tests

### Basic Commands

```bash
# Run all API unit tests
poetry run pytest tests/unit/api/ -m api

# Run specific API test file
poetry run pytest tests/unit/api/test_create_task_handler.py

# Run integration tests
poetry run pytest tests/integration/api/ -m integration

# Run end-to-end tests
poetry run pytest tests/e2e/api/ -m e2e

# Run with coverage
poetry run pytest tests/unit/api/ --cov=src.adapters.api --cov-report=html
```

### Test Execution

```bash
# Expected output for API tests
poetry run pytest tests/unit/api/ -v

# Output:
# tests/unit/api/test_create_task_handler.py::TestCreateTaskHandler::test_create_task_with_valid_request PASSED
# tests/unit/api/test_get_task_handler.py::TestGetTaskHandler::test_get_task_with_valid_id PASSED
# tests/unit/api/test_complete_task_handler.py::TestCompleteTaskHandler::test_complete_task_with_valid_id PASSED
# ...
# 60+ passed in 0.40s
```

---

## 🔄 TDD Workflow

### Step-by-Step Implementation

1. **Start with Create Task Handler**
   ```bash
   # Write test first
   poetry run pytest tests/unit/api/test_create_task_handler.py::TestCreateTaskHandler::test_create_task_with_valid_request -v
   # Test fails (expected)
   
   # Implement handler
   # Edit src/adapters/api/create_task.py
   
   # Run test again
   poetry run pytest tests/unit/api/test_create_task_handler.py::TestCreateTaskHandler::test_create_task_with_valid_request -v
   # Test passes
   ```

2. **Continue with Get Task Handler**
   ```bash
   # Write test first
   poetry run pytest tests/unit/api/test_get_task_handler.py::TestGetTaskHandler::test_get_task_with_valid_id -v
   # Test fails
   
   # Implement handler
   # Edit src/adapters/api/get_task.py
   
   # Run test again
   poetry run pytest tests/unit/api/test_get_task_handler.py::TestGetTaskHandler::test_get_task_with_valid_id -v
   # Test passes
   ```

### Verification

After implementing all API handlers:

```bash
# Run all API tests
poetry run pytest tests/unit/api/ -v

# Expected output:
# ============================= test session starts ==============================
# collected 60+ items
# tests/unit/api/test_api_utils.py ................ [ 20%]
# tests/unit/api/test_complete_task_handler.py ................ [ 40%]
# tests/unit/api/test_create_task_handler.py ................ [ 60%]
# tests/unit/api/test_get_task_handler.py ................ [ 80%]
# tests/unit/api/test_list_tasks_handler.py ................ [100%]
# ============================= 60+ passed in 0.40s ==============================
```

---

## 📊 Test Coverage Goals

- **Lambda Handlers:** 95%+ coverage
- **API Utilities:** 100% coverage
- **Error Handling:** 100% coverage
- **Integration Tests:** Critical paths only

### Coverage Report

```bash
poetry run pytest tests/unit/api/ --cov=src.adapters.api --cov-report=term-missing

# Expected coverage:
# Name                                    Stmts   Miss  Cover   Missing
# ---------------------------------------------------------------------
# src/adapters/api/create_task.py            45      0   100%
# src/adapters/api/get_task.py               35      0   100%
# src/adapters/api/complete_task.py          40      0   100%
# src/adapters/api/list_tasks.py             35      0   100%
# src/adapters/api/utils.py                  25      0   100%
# ---------------------------------------------------------------------
# TOTAL                                    180      0   100%
```

---

## 🔗 Related Files

- **Implementation:** [TUTORIAL.md](../TUTORIAL.md#api-adapter-layer-implementation)
- **Event Flow:** [EVENT_FLOW.md](../EVENT_FLOW.md)
- **Previous Layer:** [INFRASTRUCTURE_LAYER.md](INFRASTRUCTURE_LAYER.md)
- **Next Step:** [CDK_DEPLOYMENT.md](CDK_DEPLOYMENT.md) (planned)

---

## ✅ Checklist

Before moving to CDK deployment, ensure:

- [ ] All 60+ API tests pass
- [ ] All Lambda handlers are implemented and tested
- [ ] Request/response processing works correctly
- [ ] Error handling is comprehensive
- [ ] Input validation is robust
- [ ] Integration tests pass with real services
- [ ] End-to-end workflows are tested
- [ ] Test coverage is 95%+
- [ ] All tests follow TDD principles

**Next Step:** [CDK Infrastructure Implementation](../TUTORIAL.md#cdk-infrastructure-implementation) 