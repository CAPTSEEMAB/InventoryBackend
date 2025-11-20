"""
SQS Integration Module for Inventory API

This module provides SQS (Simple Queue Service) integration for:
- Reliable notification processing with retry logic
- Asynchronous background task processing
- Dead letter queue handling for failed messages
- Integration with existing SNS notification system
"""

from .sqs_client import SQSClient
from .notification_queue import NotificationQueueService
from .interfaces import QueueMessage, NotificationPayload

__all__ = [
    'SQSClient',
    'NotificationQueueService', 
    'QueueMessage',
    'NotificationPayload'
]