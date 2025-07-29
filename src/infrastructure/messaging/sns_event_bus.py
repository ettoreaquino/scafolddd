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
                    'data': event.to_dict(),
                }

                self.sns_client.publish(
                    TopicArn=self.topic_arn,
                    Subject=f'Domain Event: {event.__class__.__name__}',
                    Message=json.dumps(message),
                    MessageAttributes={
                        'event_type': {
                            'DataType': 'String',
                            'StringValue': event.__class__.__name__,
                        },
                    },
                )

                print(f"Published event: {event.__class__.__name__}")

            except Exception as e:
                print(f"Error publishing event {event.__class__.__name__}: {e}")
                raise