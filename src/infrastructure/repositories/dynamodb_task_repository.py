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
        self.table_name = table_name
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

            return bool(response.get('Attributes'))

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
