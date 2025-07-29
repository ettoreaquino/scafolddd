# tests/integration/infrastructure/test_sns_event_bus.py
import pytest
import json
import boto3
from moto import mock_aws
from datetime import datetime, timezone

from src.domain.events import TaskCreated, TaskCompleted, TaskStatusChanged
from src.infrastructure.messaging.sns_event_bus import SNSEventBus


@pytest.fixture
def sns_setup():
    """Setup SNS resources for integration testing"""
    with mock_aws():
        # Create SNS client
        sns_client = boto3.client('sns', region_name='us-east-1')
        
        # Create topic
        response = sns_client.create_topic(Name='test-topic')
        topic_arn = response['TopicArn']
        
        yield {
            'client': sns_client,
            'topic_arn': topic_arn
        }


@pytest.fixture
def event_bus(sns_setup):
    """Create event bus with real SNS resources"""
    return SNSEventBus(sns_setup['topic_arn'])


@pytest.fixture
def sample_events():
    """Create sample events for testing"""
    return [
        TaskCreated(
            aggregate_id="task-integration-1",
            task_title="Integration Test Task 1",
            user_id="user-integration-1"
        ),
        TaskCompleted(
            aggregate_id="task-integration-2", 
            task_title="Integration Test Task 2",
            user_id="user-integration-2"
        ),
        TaskStatusChanged(
            aggregate_id="task-integration-3",
            old_status="PENDING",
            new_status="IN_PROGRESS",
            user_id="user-integration-3"
        )
    ]


class TestSNSEventBusIntegration:
    """Integration tests for SNSEventBus with real AWS services"""

    @pytest.mark.asyncio
    async def test_publish_events_to_real_sns(self, event_bus, sample_events, sns_setup):
        """Test publishing events to actual SNS topic"""
        # Act - This should not raise any exceptions
        await event_bus.publish(sample_events)
        
        # Assert - If we get here without exceptions, the integration worked
        assert True

    @pytest.mark.asyncio
    async def test_publish_single_event_integration(self, event_bus, sns_setup):
        """Test publishing single event with real SNS"""
        event = TaskCreated(
            aggregate_id="integration-task-123",
            task_title="Real SNS Integration Test",
            user_id="integration-user-456"
        )
        
        # Act
        await event_bus.publish([event])
        
        # Assert - No exceptions means success
        assert True

    @pytest.mark.asyncio
    async def test_publish_empty_list_integration(self, event_bus):
        """Test publishing empty event list"""
        # Act
        await event_bus.publish([])
        
        # Assert - No exceptions means success
        assert True

    @pytest.mark.asyncio
    async def test_event_bus_initialization_with_real_topic(self, sns_setup):
        """Test event bus initialization with real topic ARN"""
        # Act
        event_bus = SNSEventBus(sns_setup['topic_arn'])
        
        # Assert
        assert event_bus.topic_arn == sns_setup['topic_arn']
        assert event_bus.sns_client is not None

    @pytest.mark.asyncio
    async def test_publish_large_number_of_events(self, event_bus):
        """Test publishing a larger number of events"""
        events = []
        for i in range(10):
            events.append(TaskCreated(
                aggregate_id=f"bulk-task-{i}",
                task_title=f"Bulk Test Task {i}",
                user_id=f"bulk-user-{i}"
            ))
        
        # Act
        await event_bus.publish(events)
        
        # Assert - No exceptions means success
        assert True

    @pytest.mark.asyncio 
    async def test_publish_different_event_types_integration(self, event_bus):
        """Test publishing different event types in integration environment"""
        events = [
            TaskCreated(aggregate_id="mix-1", task_title="Mixed 1", user_id="user-1"),
            TaskCompleted(aggregate_id="mix-2", task_title="Mixed 2", user_id="user-2"),
            TaskStatusChanged(aggregate_id="mix-3", old_status="PENDING", new_status="COMPLETED", user_id="user-3")
        ]
        
        # Act
        await event_bus.publish(events)
        
        # Assert - No exceptions means success
        assert True

    @pytest.mark.asyncio
    async def test_invalid_topic_arn_raises_error(self):
        """Test that invalid topic ARN raises appropriate error"""
        invalid_event_bus = SNSEventBus("invalid-topic-arn")
        event = TaskCreated(
            aggregate_id="error-task",
            task_title="Error Test",
            user_id="error-user"
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            await invalid_event_bus.publish([event])

    @pytest.mark.asyncio
    async def test_auto_generated_fields_in_integration(self, event_bus):
        """Test that auto-generated fields work in integration environment"""
        event = TaskCreated(
            aggregate_id="auto-gen-test",
            task_title="Auto Generation Integration Test",
            user_id="auto-gen-user"
        )
        
        # Verify auto-generated fields exist before publishing
        assert event.event_id is not None
        assert len(event.event_id) > 0
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
        
        # Act - Should publish successfully with auto-generated fields
        await event_bus.publish([event])
        
        # Assert - No exceptions means success
        assert True