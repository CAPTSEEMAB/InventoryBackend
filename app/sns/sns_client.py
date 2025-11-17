"""
Simple AWS SNS client for publishing messages
"""

import boto3
import os
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from .interfaces import NotificationProvider

# Load environment variables
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)


class SNSClient(NotificationProvider):
    """Simple AWS SNS implementation for publishing messages"""
    
    def __init__(self, region_name: str = None):
        """Initialize SNS client"""
        self.region_name = region_name or os.getenv('AWS_SNS_REGION', 'us-east-1')
        self.sns_client = boto3.client(
            'sns',
            region_name=self.region_name,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self._topic_cache = {}
    
    def publish_message(self, topic: str, message: str, subject: str = None) -> bool:
        """Publish a message to an SNS topic"""
        try:
            topic_arn = self._get_or_create_topic(topic)
            if not topic_arn:
                return False
            
            publish_params = {
                'TopicArn': topic_arn,
                'Message': message
            }
            
            if subject:
                publish_params['Subject'] = subject
            
            response = self.sns_client.publish(**publish_params)
            return response.get('MessageId') is not None
            
        except ClientError as e:
            print(f"SNS publish error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error in SNS publish: {e}")
            return False
    
    def _get_or_create_topic(self, topic_name: str) -> str:
        """Get existing topic ARN or create new topic"""
        if topic_name in self._topic_cache:
            return self._topic_cache[topic_name]
        
        try:
            # Try to create topic (idempotent operation)
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            self._topic_cache[topic_name] = topic_arn
            return topic_arn
            
        except ClientError as e:
            print(f"SNS topic error: {e}")
            return ""