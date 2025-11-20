"""
Notification Queue Service for reliable email delivery with retry logic
Integrates with existing SNS system to provide guaranteed delivery
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from .sqs_client import SQSClient
from .interfaces import QueueMessage, NotificationPayload

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)


class NotificationQueueService:
    """Service for reliable notification delivery using SQS"""
    
    def __init__(self):
        self.sqs_client = SQSClient()
        self.enabled = os.getenv('SQS_ENABLE_NOTIFICATIONS', 'true').lower() == 'true'
        
        # Queue names
        self.notification_queue = 'notification-processing-queue'
        self.dlq_queue = 'notification-dead-letter-queue'
        
        # Initialize queues if enabled
        if self.enabled:
            self._ensure_queues_exist()
    
    def _ensure_queues_exist(self):
        """Ensure required queues exist"""
        try:
            # Create dead letter queue first
            dlq_url = self.sqs_client.create_queue(
                queue_name=self.dlq_queue,
                visibility_timeout=60,
                message_retention_period=1209600  # 14 days
            )
            
            # Get DLQ ARN for main queue
            dlq_arn = self._get_queue_arn(self.dlq_queue)
            
            # Create main notification queue with DLQ
            self.sqs_client.create_queue(
                queue_name=self.notification_queue,
                dead_letter_queue_arn=dlq_arn,
                visibility_timeout=30,
                message_retention_period=1209600  # 14 days
            )
            
        except Exception as e:
            pass
    
    def _get_queue_arn(self, queue_name: str) -> Optional[str]:
        """Get queue ARN from queue name"""
        try:
            return f"arn:aws:sqs:{self.sqs_client.region}:{self.sqs_client.account_id}:{queue_name}"
        except Exception:
            return None
    
    def queue_notification(self, notification: NotificationPayload, 
                          delay_seconds: int = 0, priority: str = "normal") -> bool:
        """
        Queue a notification for reliable delivery
        
        Args:
            notification: Notification payload to queue
            delay_seconds: Delay delivery by specified seconds
            priority: Priority level (normal, high, low)
            
        Returns:
            True if queued successfully, False otherwise
        """
        if not self.enabled:
            return self._send_direct_notification(notification)
        
        try:
            # Create queue message
            message = QueueMessage(
                id=str(uuid.uuid4()),
                message_type="email_notification",
                payload={
                    "notification": notification.model_dump(),
                    "priority": priority,
                    "queued_at": datetime.now().isoformat()
                },
                retry_count=0,
                max_retries=3,
                created_at=datetime.now()
            )
            
            # Send to SQS
            success = self.sqs_client.send_message(
                queue_name=self.notification_queue,
                message=message,
                delay_seconds=delay_seconds
            )
            
            return success
            
        except Exception as e:
            # Fallback to direct notification if queuing fails
            return self._send_direct_notification(notification)
    
    def _send_direct_notification(self, notification: NotificationPayload) -> bool:
        """
        Fallback: Send notification directly without queue
        
        Args:
            notification: Notification to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from ..sns.service import ProductNotificationService
            
            sns_service = ProductNotificationService()
            
            # Convert notification to SNS format
            success = sns_service._send_email_notification(
                email=notification.recipient_email,
                subject=notification.subject,
                message=notification.message
            )
            
            return success
            
        except Exception as e:
            return False
    
    def process_queued_notifications(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Process a batch of queued notifications
        
        Args:
            batch_size: Number of messages to process in this batch
            
        Returns:
            Processing results summary
        """
        if not self.enabled:
            return {"status": "disabled", "processed": 0}
        
        try:
            # Receive messages from queue
            messages = self.sqs_client.receive_messages(
                queue_name=self.notification_queue,
                max_messages=min(batch_size, 10),
                wait_time=5  # Short polling for background processing
            )
            
            results = {
                "status": "success",
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "retried": 0,
                "errors": []
            }
            
            for msg_data in messages:
                message = msg_data['message']
                receipt_handle = msg_data['receipt_handle']
                
                try:
                    # Extract notification payload
                    notification_data = message.payload.get('notification', {})
                    notification = NotificationPayload.model_validate(notification_data)
                    
                    # Attempt to send notification
                    success = self._send_email_notification(notification)
                    
                    if success:
                        # Delete message on successful processing
                        self.sqs_client.delete_message(self.notification_queue, receipt_handle)
                        results["successful"] += 1
                    else:
                        # Handle retry logic
                        if message.retry_count < message.max_retries:
                            # Increment retry count and requeue with delay
                            message.retry_count += 1
                            message.error_message = "Email delivery failed, retrying"
                            
                            retry_delay = self._calculate_retry_delay(message.retry_count)
                            
                            # Delete original message and send new one with retry count
                            self.sqs_client.delete_message(self.notification_queue, receipt_handle)
                            self.sqs_client.send_message(
                                queue_name=self.notification_queue,
                                message=message,
                                delay_seconds=retry_delay
                            )
                            
                            results["retried"] += 1
                        else:
                            # Max retries exceeded, message will go to DLQ
                            results["failed"] += 1
                            results["errors"].append(f"Max retries exceeded for {notification.recipient_email}")
                    
                    results["processed"] += 1
                    
                except Exception as processing_error:
                    # Delete malformed messages
                    self.sqs_client.delete_message(self.notification_queue, receipt_handle)
                    results["failed"] += 1
                    results["errors"].append(f"Processing error: {str(processing_error)}")
            
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "processed": 0
            }
    
    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        Calculate exponential backoff delay for retries
        
        Args:
            retry_count: Current retry attempt number
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: 30s, 2m, 8m
        base_delay = 30
        return min(base_delay * (2 ** (retry_count - 1)), 480)  # Max 8 minutes
    
    def _send_email_notification(self, notification: NotificationPayload) -> bool:
        """
        Send individual email notification using existing SNS infrastructure
        
        Args:
            notification: Notification to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Import here to avoid circular imports
            import boto3
            
            # Use SNS directly for email delivery
            sns_client = boto3.client(
                'sns',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_SNS_REGION', 'us-east-1')
            )
            
            # Get the notification topic ARN
            topic_name = "product-notifications"
            topic_arn = self._get_sns_topic_arn(topic_name)
            
            if not topic_arn:
                return False
            
            # Publish to SNS topic (which delivers to email subscribers)
            sns_client.publish(
                TopicArn=topic_arn,
                Subject=notification.subject,
                Message=notification.message
            )
            
            return True
            
        except Exception as e:
            return False
    
    def _get_sns_topic_arn(self, topic_name: str) -> Optional[str]:
        """Get SNS topic ARN"""
        try:
            import boto3
            
            sns_client = boto3.client(
                'sns',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_SNS_REGION', 'us-east-1')
            )
            
            response = sns_client.list_topics()
            for topic in response.get('Topics', []):
                arn = topic['TopicArn']
                if arn.endswith(f":{topic_name}"):
                    return arn
            
            return None
            
        except Exception:
            return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics for notification queues
        
        Returns:
            Dictionary with queue statistics
        """
        if not self.enabled:
            return {"status": "disabled"}
        
        try:
            main_stats = self.sqs_client.get_queue_stats(self.notification_queue)
            dlq_stats = self.sqs_client.get_queue_stats(self.dlq_queue)
            
            return {
                "status": "enabled",
                "notification_queue": main_stats.model_dump() if main_stats else None,
                "dead_letter_queue": dlq_stats.model_dump() if dlq_stats else None,
                "total_pending": main_stats.visible_messages if main_stats else 0,
                "total_failed": dlq_stats.visible_messages if dlq_stats else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def requeue_failed_messages(self, max_messages: int = 10) -> Dict[str, Any]:
        """
        Requeue messages from dead letter queue for retry
        
        Args:
            max_messages: Maximum messages to requeue
            
        Returns:
            Requeue results
        """
        if not self.enabled:
            return {"status": "disabled", "requeued": 0}
        
        try:
            # Get messages from DLQ
            dlq_messages = self.sqs_client.receive_messages(
                queue_name=self.dlq_queue,
                max_messages=max_messages,
                wait_time=5
            )
            
            requeued = 0
            
            for msg_data in dlq_messages:
                try:
                    message = msg_data['message']
                    receipt_handle = msg_data['receipt_handle']
                    
                    # Reset retry count and requeue
                    message.retry_count = 0
                    message.error_message = "Requeued from DLQ"
                    
                    success = self.sqs_client.send_message(
                        queue_name=self.notification_queue,
                        message=message
                    )
                    
                    if success:
                        # Delete from DLQ after successful requeue
                        self.sqs_client.delete_message(self.dlq_queue, receipt_handle)
                        requeued += 1
                
                except Exception:
                    continue
            
            return {
                "status": "success",
                "requeued": requeued,
                "available_in_dlq": len(dlq_messages)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "requeued": 0
            }