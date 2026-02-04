import pytest
import os
import json
import boto3
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
from src.infrastructure.messaging.sns_event_bus import SNSEventBus
from src.domain.events import TaskCreated, TaskCompleted, TaskStatusChanged


# ============================================================================
# Test Constants
# ============================================================================

TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:test-topic"


# ============================================================================
# Helpers
# ============================================================================

def create_task_created_event(
    event_id: str = "evt-123",
    aggregate_id: str = "task-456",
    task_title: str = "Test Task",
    user_id: str = "user-789",
) -> TaskCreated:
    """Create a TaskCreated event for testing"""
    return TaskCreated(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc),
        aggregate_id=aggregate_id,
        task_title=task_title,
        user_id=user_id,
    )


def create_task_completed_event(
    event_id: str = "evt-456",
    aggregate_id: str = "task-456",
    task_title: str = "Test Task",
    user_id: str = "user-789",
) -> TaskCompleted:
    """Create a TaskCompleted event for testing"""
    return TaskCompleted(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc),
        aggregate_id=aggregate_id,
        task_title=task_title,
        user_id=user_id,
    )


def create_task_status_changed_event(
    event_id: str = "evt-789",
    aggregate_id: str = "task-456",
    old_status: str = "pending",
    new_status: str = "completed",
    user_id: str = "user-789",
) -> TaskStatusChanged:
    """Create a TaskStatusChanged event for testing"""
    return TaskStatusChanged(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc),
        aggregate_id=aggregate_id,
        old_status=old_status,
        new_status=new_status,
        user_id=user_id,
    )


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def aws_credentials():
    """Set mock AWS credentials for moto"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield


@pytest.fixture
def mock_sns():
    """Create a mocked SNS environment"""
    with mock_aws():
        client = boto3.client('sns', region_name='us-east-1')
        topic = client.create_topic(Name='test-topic')
        topic_arn = topic['TopicArn']
        yield topic_arn


@pytest.fixture
def event_bus(mock_sns):
    """Create an SNSEventBus with mocked SNS"""
    return SNSEventBus(mock_sns)


# ============================================================================
# Test: Event Bus Interface Compliance
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestSNSEventBusInterfaceCompliance:
    """Test that SNSEventBus implements the EventBus interface"""

    def test_event_bus_has_publish_method(self, event_bus):
        """Test that event bus has a publish method"""
        assert hasattr(event_bus, 'publish')
        assert callable(getattr(event_bus, 'publish'))

    def test_event_bus_stores_topic_arn(self, event_bus, mock_sns):
        """Test that event bus stores the topic ARN"""
        assert event_bus.topic_arn == mock_sns

    def test_event_bus_has_sns_client(self, event_bus):
        """Test that event bus has an SNS client"""
        assert event_bus.sns_client is not None


# ============================================================================
# Test: Event Serialization
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestSNSEventSerialization:
    """Test event serialization for SNS publishing"""

    @pytest.mark.asyncio
    async def test_publish_task_created_event(self, event_bus):
        """Test publishing a TaskCreated event"""
        event = create_task_created_event()
        await event_bus.publish([event])
        # No exception means success

    @pytest.mark.asyncio
    async def test_publish_task_completed_event(self, event_bus):
        """Test publishing a TaskCompleted event"""
        event = create_task_completed_event()
        await event_bus.publish([event])

    @pytest.mark.asyncio
    async def test_publish_task_status_changed_event(self, event_bus):
        """Test publishing a TaskStatusChanged event"""
        event = create_task_status_changed_event()
        await event_bus.publish([event])

    @pytest.mark.asyncio
    async def test_publish_event_message_contains_event_type(self):
        """Test that published message contains event type"""
        with mock_aws():
            client = boto3.client('sns', region_name='us-east-1')
            topic = client.create_topic(Name='test-topic')
            topic_arn = topic['TopicArn']

            # Subscribe an SQS queue to capture messages
            sqs = boto3.resource('sqs', region_name='us-east-1')
            queue = sqs.create_queue(QueueName='test-queue')
            sqs_client = boto3.client('sqs', region_name='us-east-1')
            queue_arn = sqs_client.get_queue_attributes(
                QueueUrl=queue.url,
                AttributeNames=['QueueArn']
            )['Attributes']['QueueArn']

            client.subscribe(
                TopicArn=topic_arn,
                Protocol='sqs',
                Endpoint=queue_arn
            )

            event_bus = SNSEventBus(topic_arn)
            event = create_task_created_event()
            await event_bus.publish([event])

            # Receive message from SQS
            messages = sqs_client.receive_message(
                QueueUrl=queue.url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=0
            )

            assert 'Messages' in messages
            body = json.loads(messages['Messages'][0]['Body'])
            message = json.loads(body['Message'])
            assert message['event_type'] == 'TaskCreated'

    @pytest.mark.asyncio
    async def test_publish_event_message_contains_event_data(self):
        """Test that published message contains event data"""
        with mock_aws():
            client = boto3.client('sns', region_name='us-east-1')
            topic = client.create_topic(Name='test-topic')
            topic_arn = topic['TopicArn']

            sqs = boto3.resource('sqs', region_name='us-east-1')
            queue = sqs.create_queue(QueueName='test-queue')
            sqs_client = boto3.client('sqs', region_name='us-east-1')
            queue_arn = sqs_client.get_queue_attributes(
                QueueUrl=queue.url,
                AttributeNames=['QueueArn']
            )['Attributes']['QueueArn']

            client.subscribe(
                TopicArn=topic_arn,
                Protocol='sqs',
                Endpoint=queue_arn
            )

            event_bus = SNSEventBus(topic_arn)
            event = create_task_created_event(
                event_id="evt-test",
                aggregate_id="task-test",
                task_title="My Task",
                user_id="user-test",
            )
            await event_bus.publish([event])

            messages = sqs_client.receive_message(
                QueueUrl=queue.url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=0
            )

            body = json.loads(messages['Messages'][0]['Body'])
            message = json.loads(body['Message'])
            assert message['event_id'] == 'evt-test'
            assert message['aggregate_id'] == 'task-test'
            assert 'timestamp' in message
            assert 'data' in message
            assert message['data']['task_title'] == 'My Task'
            assert message['data']['user_id'] == 'user-test'


# ============================================================================
# Test: Multiple Events Publishing
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestSNSMultipleEventsPublishing:
    """Test publishing multiple events"""

    @pytest.mark.asyncio
    async def test_publish_multiple_events_succeeds(self, event_bus):
        """Test publishing multiple events at once"""
        events = [
            create_task_created_event(event_id="evt-1"),
            create_task_completed_event(event_id="evt-2"),
        ]
        await event_bus.publish(events)

    @pytest.mark.asyncio
    async def test_publish_empty_event_list(self, event_bus):
        """Test publishing an empty list of events"""
        await event_bus.publish([])
        # Should succeed without any SNS calls

    @pytest.mark.asyncio
    async def test_publish_three_different_event_types(self, event_bus):
        """Test publishing all three event types at once"""
        events = [
            create_task_created_event(event_id="evt-1"),
            create_task_status_changed_event(event_id="evt-2"),
            create_task_completed_event(event_id="evt-3"),
        ]
        await event_bus.publish(events)

    @pytest.mark.asyncio
    async def test_publish_multiple_events_sends_correct_count(self):
        """Test that multiple events result in the correct number of SNS publishes"""
        with mock_aws():
            client = boto3.client('sns', region_name='us-east-1')
            topic = client.create_topic(Name='test-topic')
            topic_arn = topic['TopicArn']

            sqs = boto3.resource('sqs', region_name='us-east-1')
            queue = sqs.create_queue(QueueName='test-queue')
            sqs_client = boto3.client('sqs', region_name='us-east-1')
            queue_arn = sqs_client.get_queue_attributes(
                QueueUrl=queue.url,
                AttributeNames=['QueueArn']
            )['Attributes']['QueueArn']

            client.subscribe(
                TopicArn=topic_arn,
                Protocol='sqs',
                Endpoint=queue_arn
            )

            event_bus = SNSEventBus(topic_arn)
            events = [
                create_task_created_event(event_id="evt-1"),
                create_task_completed_event(event_id="evt-2"),
            ]
            await event_bus.publish(events)

            messages = sqs_client.receive_message(
                QueueUrl=queue.url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=0
            )

            assert 'Messages' in messages
            assert len(messages['Messages']) == 2

            event_types = set()
            for msg in messages['Messages']:
                body = json.loads(msg['Body'])
                message = json.loads(body['Message'])
                event_types.add(message['event_type'])

            assert 'TaskCreated' in event_types
            assert 'TaskCompleted' in event_types


# ============================================================================
# Test: Error Handling
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestSNSErrorHandling:
    """Test SNS error handling"""

    @pytest.mark.asyncio
    async def test_publish_raises_on_sns_error(self):
        """Test that SNS errors are propagated"""
        with mock_aws():
            # Use an invalid topic ARN to trigger an error
            event_bus = SNSEventBus("arn:aws:sns:us-east-1:123456789012:nonexistent-topic")
            event = create_task_created_event()

            with pytest.raises(Exception):
                await event_bus.publish([event])

    @pytest.mark.asyncio
    async def test_publish_with_mock_sns_error(self):
        """Test that SNS client errors are raised"""
        mock_client = Mock()
        mock_client.publish.side_effect = Exception("SNS service error")

        event_bus = SNSEventBus.__new__(SNSEventBus)
        event_bus.sns_client = mock_client
        event_bus.topic_arn = TOPIC_ARN

        event = create_task_created_event()

        with pytest.raises(Exception, match="SNS service error"):
            await event_bus.publish([event])

    @pytest.mark.asyncio
    async def test_publish_error_includes_event_info(self):
        """Test that errors are raised after logging event info"""
        mock_client = Mock()
        mock_client.publish.side_effect = RuntimeError("Connection timeout")

        event_bus = SNSEventBus.__new__(SNSEventBus)
        event_bus.sns_client = mock_client
        event_bus.topic_arn = TOPIC_ARN

        event = create_task_created_event()

        with pytest.raises(RuntimeError, match="Connection timeout"):
            await event_bus.publish([event])


# ============================================================================
# Test: Message Attributes
# ============================================================================

@pytest.mark.infrastructure
@pytest.mark.unit
class TestSNSMessageAttributes:
    """Test SNS message attributes"""

    @pytest.mark.asyncio
    async def test_publish_includes_event_type_attribute(self):
        """Test that published message includes event_type in MessageAttributes"""
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'test-msg-id'}

        event_bus = SNSEventBus.__new__(SNSEventBus)
        event_bus.sns_client = mock_client
        event_bus.topic_arn = TOPIC_ARN

        event = create_task_created_event()
        await event_bus.publish([event])

        call_kwargs = mock_client.publish.call_args[1]
        assert 'MessageAttributes' in call_kwargs
        assert 'event_type' in call_kwargs['MessageAttributes']
        assert call_kwargs['MessageAttributes']['event_type']['StringValue'] == 'TaskCreated'
        assert call_kwargs['MessageAttributes']['event_type']['DataType'] == 'String'

    @pytest.mark.asyncio
    async def test_publish_includes_correct_topic_arn(self):
        """Test that published message uses the correct topic ARN"""
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'test-msg-id'}

        event_bus = SNSEventBus.__new__(SNSEventBus)
        event_bus.sns_client = mock_client
        event_bus.topic_arn = TOPIC_ARN

        event = create_task_created_event()
        await event_bus.publish([event])

        call_kwargs = mock_client.publish.call_args[1]
        assert call_kwargs['TopicArn'] == TOPIC_ARN

    @pytest.mark.asyncio
    async def test_publish_includes_subject(self):
        """Test that published message includes a subject"""
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'test-msg-id'}

        event_bus = SNSEventBus.__new__(SNSEventBus)
        event_bus.sns_client = mock_client
        event_bus.topic_arn = TOPIC_ARN

        event = create_task_created_event()
        await event_bus.publish([event])

        call_kwargs = mock_client.publish.call_args[1]
        assert 'Subject' in call_kwargs
        assert 'TaskCreated' in call_kwargs['Subject']

    @pytest.mark.asyncio
    async def test_publish_message_is_valid_json(self):
        """Test that the published message body is valid JSON"""
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'test-msg-id'}

        event_bus = SNSEventBus.__new__(SNSEventBus)
        event_bus.sns_client = mock_client
        event_bus.topic_arn = TOPIC_ARN

        event = create_task_created_event()
        await event_bus.publish([event])

        call_kwargs = mock_client.publish.call_args[1]
        message = json.loads(call_kwargs['Message'])

        assert 'event_type' in message
        assert 'event_id' in message
        assert 'aggregate_id' in message
        assert 'timestamp' in message
        assert 'data' in message
