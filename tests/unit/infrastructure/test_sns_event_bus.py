# tests/unit/infrastructure/test_sns_event_bus.py
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.domain.events import TaskCreated, TaskCompleted, TaskStatusChanged
from src.infrastructure.messaging.sns_event_bus import SNSEventBus


# Test fixtures
@pytest.fixture
def topic_arn():
    """Test SNS topic ARN"""
    return "arn:aws:sns:us-east-1:123456789012:test-topic"


@pytest.fixture
def mock_sns_client():
    """Mock SNS client"""
    return Mock()


@pytest.fixture
def event_bus(topic_arn, mock_sns_client):
    """Create SNS event bus with mocked client"""
    with patch('boto3.client', return_value=mock_sns_client):
        return SNSEventBus(topic_arn)


@pytest.fixture
def task_created_event():
    """Create a TaskCreated event for testing"""
    return TaskCreated(
        aggregate_id="task-123",
        task_title="Test Task",
        user_id="user-456"
    )


@pytest.fixture
def task_completed_event():
    """Create a TaskCompleted event for testing"""
    return TaskCompleted(
        aggregate_id="task-123",
        task_title="Test Task",
        user_id="user-456"
    )


@pytest.fixture
def task_status_changed_event():
    """Create a TaskStatusChanged event for testing"""
    return TaskStatusChanged(
        aggregate_id="task-123",
        old_status="PENDING",
        new_status="IN_PROGRESS",
        user_id="user-456"
    )


class TestSNSEventBus:
    """Test cases for SNSEventBus"""

    @pytest.mark.asyncio
    async def test_publish_single_event(self, event_bus, task_created_event, mock_sns_client, topic_arn):
        """Test publishing a single event"""
        # Act
        await event_bus.publish([task_created_event])
        
        # Assert
        mock_sns_client.publish.assert_called_once()
        call_args = mock_sns_client.publish.call_args
        
        assert call_args[1]['TopicArn'] == topic_arn
        assert call_args[1]['Subject'] == 'Domain Event: TaskCreated'
        
        # Verify message structure
        message = json.loads(call_args[1]['Message'])
        assert message['event_type'] == 'TaskCreated'
        assert message['aggregate_id'] == 'task-123'
        assert 'event_id' in message
        assert 'timestamp' in message
        assert message['data']['task_title'] == 'Test Task'
        assert message['data']['user_id'] == 'user-456'
        
        # Verify message attributes
        assert call_args[1]['MessageAttributes']['event_type']['DataType'] == 'String'
        assert call_args[1]['MessageAttributes']['event_type']['StringValue'] == 'TaskCreated'

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, event_bus, task_created_event, task_completed_event, mock_sns_client):
        """Test publishing multiple events"""
        events = [task_created_event, task_completed_event]
        
        # Act
        await event_bus.publish(events)
        
        # Assert
        assert mock_sns_client.publish.call_count == 2
        
        # Verify first event (TaskCreated)
        first_call = mock_sns_client.publish.call_args_list[0]
        first_message = json.loads(first_call[1]['Message'])
        assert first_message['event_type'] == 'TaskCreated'
        
        # Verify second event (TaskCompleted)
        second_call = mock_sns_client.publish.call_args_list[1]
        second_message = json.loads(second_call[1]['Message'])
        assert second_message['event_type'] == 'TaskCompleted'

    @pytest.mark.asyncio
    async def test_publish_task_status_changed_event(self, event_bus, task_status_changed_event, mock_sns_client):
        """Test publishing TaskStatusChanged event with specific data"""
        # Act
        await event_bus.publish([task_status_changed_event])
        
        # Assert
        call_args = mock_sns_client.publish.call_args
        message = json.loads(call_args[1]['Message'])
        
        assert message['event_type'] == 'TaskStatusChanged'
        assert message['data']['old_status'] == 'PENDING'
        assert message['data']['new_status'] == 'IN_PROGRESS'
        assert message['data']['user_id'] == 'user-456'

    @pytest.mark.asyncio
    async def test_publish_empty_events_list(self, event_bus, mock_sns_client):
        """Test publishing empty events list"""
        # Act
        await event_bus.publish([])
        
        # Assert
        mock_sns_client.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_handles_sns_error(self, event_bus, task_created_event, mock_sns_client):
        """Test error handling when SNS publish fails"""
        # Arrange
        mock_sns_client.publish.side_effect = Exception("SNS publish failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await event_bus.publish([task_created_event])
        
        assert "SNS publish failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_event_message_structure(self, event_bus, task_created_event, mock_sns_client):
        """Test the complete message structure"""
        # Act
        await event_bus.publish([task_created_event])
        
        # Assert
        call_args = mock_sns_client.publish.call_args
        message = json.loads(call_args[1]['Message'])
        
        # Verify all required fields are present
        required_fields = ['event_type', 'event_id', 'aggregate_id', 'timestamp', 'data']
        for field in required_fields:
            assert field in message
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(message['timestamp'])
        assert isinstance(timestamp, datetime)
        
        # Verify event data structure
        assert isinstance(message['data'], dict)
        assert 'task_title' in message['data']
        assert 'user_id' in message['data']

    @pytest.mark.asyncio
    async def test_message_attributes_structure(self, event_bus, task_created_event, mock_sns_client):
        """Test SNS message attributes structure"""
        # Act
        await event_bus.publish([task_created_event])
        
        # Assert
        call_args = mock_sns_client.publish.call_args
        message_attributes = call_args[1]['MessageAttributes']
        
        assert 'event_type' in message_attributes
        assert message_attributes['event_type']['DataType'] == 'String'
        assert message_attributes['event_type']['StringValue'] == 'TaskCreated'

    def test_init_creates_sns_client(self, topic_arn):
        """Test that initialization creates SNS client"""
        with patch('boto3.client') as mock_boto3_client:
            event_bus = SNSEventBus(topic_arn)
            
            mock_boto3_client.assert_called_once_with('sns')
            assert event_bus.topic_arn == topic_arn

    @pytest.mark.asyncio
    async def test_publish_with_different_event_types(self, event_bus, mock_sns_client):
        """Test publishing different types of events"""
        events = [
            TaskCreated(aggregate_id="task-1", task_title="Task 1", user_id="user-1"),
            TaskCompleted(aggregate_id="task-2", task_title="Task 2", user_id="user-2"),
            TaskStatusChanged(aggregate_id="task-3", old_status="PENDING", new_status="COMPLETED", user_id="user-3")
        ]
        
        # Act
        await event_bus.publish(events)
        
        # Assert
        assert mock_sns_client.publish.call_count == 3
        
        # Verify each event type was published correctly
        calls = mock_sns_client.publish.call_args_list
        
        # First event - TaskCreated
        first_message = json.loads(calls[0][1]['Message'])
        assert first_message['event_type'] == 'TaskCreated'
        assert first_message['aggregate_id'] == 'task-1'
        
        # Second event - TaskCompleted
        second_message = json.loads(calls[1][1]['Message'])
        assert second_message['event_type'] == 'TaskCompleted'
        assert second_message['aggregate_id'] == 'task-2'
        
        # Third event - TaskStatusChanged
        third_message = json.loads(calls[2][1]['Message'])
        assert third_message['event_type'] == 'TaskStatusChanged'
        assert third_message['aggregate_id'] == 'task-3'
        assert third_message['data']['old_status'] == 'PENDING'
        assert third_message['data']['new_status'] == 'COMPLETED'

    @pytest.mark.asyncio
    async def test_publish_preserves_event_data_integrity(self, event_bus, mock_sns_client):
        """Test that event data is preserved correctly during publishing"""
        # Create event with specific data
        event = TaskCreated(
            aggregate_id="task-special-chars-123!@#",
            task_title="Task with special chars: !@#$%^&*()",
            user_id="user-with-dashes-and-numbers-123"
        )
        
        # Act
        await event_bus.publish([event])
        
        # Assert
        call_args = mock_sns_client.publish.call_args
        message = json.loads(call_args[1]['Message'])
        
        assert message['aggregate_id'] == "task-special-chars-123!@#"
        assert message['data']['task_title'] == "Task with special chars: !@#$%^&*()"
        assert message['data']['user_id'] == "user-with-dashes-and-numbers-123"

    @pytest.mark.asyncio
    async def test_event_auto_generation_works(self, event_bus, mock_sns_client):
        """Test that event_id and timestamp are auto-generated"""
        # Create event without specifying event_id or timestamp
        event = TaskCreated(
            aggregate_id="test-task",
            task_title="Auto Generation Test", 
            user_id="test-user"
        )
        
        # Verify auto-generated fields exist
        assert event.event_id is not None
        assert len(event.event_id) > 0
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
        
        # Act
        await event_bus.publish([event])
        
        # Assert
        call_args = mock_sns_client.publish.call_args
        message = json.loads(call_args[1]['Message'])
        
        assert message['event_id'] == event.event_id
        assert message['timestamp'] == event.timestamp.isoformat()

    @pytest.mark.asyncio
    async def test_event_override_works_for_testing(self, event_bus, mock_sns_client):
        """Test that we can override event_id and timestamp for testing"""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        fixed_id = "test-event-123"
        
        # Create event with fixed values for testing
        event = TaskCreated(
            aggregate_id="test-task",
            task_title="Override Test",
            user_id="test-user", 
            event_id=fixed_id,
            timestamp=fixed_time
        )
        
        # Verify values are as expected
        assert event.event_id == fixed_id
        assert event.timestamp == fixed_time
        
        # Act
        await event_bus.publish([event])
        
        # Assert
        call_args = mock_sns_client.publish.call_args
        message = json.loads(call_args[1]['Message'])
        
        assert message['event_id'] == fixed_id
        assert message['timestamp'] == fixed_time.isoformat()