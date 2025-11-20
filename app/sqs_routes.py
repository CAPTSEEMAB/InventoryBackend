"""
SQS Routes for Queue Management and Monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from .utils import ok, bad
from .auth import get_current_user
from .sqs.notification_queue import NotificationQueueService
from .sqs.interfaces import NotificationPayload
from .sqs.worker import get_notification_worker

router = APIRouter(prefix="/sqs", tags=["SQS Queue Management"])

# Initialize services
try:
    notification_service = NotificationQueueService()
except Exception as e:
    notification_service = None


class QueueNotificationRequest(BaseModel):
    recipient_email: str
    subject: str
    message: str
    notification_type: str = "product_notification"
    delay_seconds: int = 0
    priority: str = "normal"


class RequeueRequest(BaseModel):
    max_messages: int = 10


@router.get("/")
def sqs_overview(current=Depends(get_current_user)):
    """Get SQS service overview"""
    if not notification_service or not notification_service.enabled:
        return ok("SQS service status", {
            "enabled": False,
            "message": "SQS notification queuing is disabled"
        })
    
    return ok("SQS service overview", {
        "enabled": True,
        "notification_queue": notification_service.notification_queue,
        "dead_letter_queue": notification_service.dlq_queue,
        "endpoints": [
            "/api/sqs/stats - Queue statistics",
            "/api/sqs/notification - Queue notification manually", 
            "/api/sqs/worker/stats - Background worker status",
            "/api/sqs/requeue - Requeue failed messages",
            "/api/sqs/process - Process notifications manually"
        ]
    })


@router.get("/stats")
def get_queue_stats(current=Depends(get_current_user)):
    """Get comprehensive queue statistics"""
    if not notification_service:
        return bad(503, "SERVICE_UNAVAILABLE", "SQS service not initialized")
    
    try:
        stats = notification_service.get_queue_stats()
        return ok("Queue statistics retrieved", stats)
        
    except Exception as e:
        return bad(500, "QUEUE_ERROR", "Failed to retrieve queue statistics", str(e))


@router.post("/notification")
def queue_notification_manually(
    request: QueueNotificationRequest,
    current=Depends(get_current_user)
):
    """Manually queue a notification for testing"""
    if not notification_service:
        return bad(503, "SERVICE_UNAVAILABLE", "SQS service not initialized")
    
    try:
        # Create notification payload
        notification = NotificationPayload(
            recipient_email=request.recipient_email,
            subject=request.subject,
            message=request.message,
            notification_type=request.notification_type
        )
        
        # Queue the notification
        success = notification_service.queue_notification(
            notification=notification,
            delay_seconds=request.delay_seconds,
            priority=request.priority
        )
        
        if success:
            return ok("Notification queued successfully", {
                "queued": True,
                "recipient": request.recipient_email,
                "delay_seconds": request.delay_seconds,
                "priority": request.priority
            })
        else:
            return bad(500, "QUEUE_ERROR", "Failed to queue notification")
            
    except Exception as e:
        return bad(500, "QUEUE_ERROR", "Failed to queue notification", str(e))


@router.post("/process")
def process_notifications_manually(current=Depends(get_current_user)):
    """Manually trigger notification processing"""
    if not notification_service:
        return bad(503, "SERVICE_UNAVAILABLE", "SQS service not initialized")
    
    try:
        results = notification_service.process_queued_notifications(batch_size=10)
        return ok("Batch processing completed", results)
        
    except Exception as e:
        return bad(500, "PROCESSING_ERROR", "Failed to process notifications", str(e))


@router.post("/requeue")
def requeue_failed_messages(
    request: RequeueRequest,
    current=Depends(get_current_user)
):
    """Requeue failed messages from dead letter queue"""
    if not notification_service:
        return bad(503, "SERVICE_UNAVAILABLE", "SQS service not initialized")
    
    try:
        results = notification_service.requeue_failed_messages(request.max_messages)
        return ok("Requeue operation completed", results)
        
    except Exception as e:
        return bad(500, "REQUEUE_ERROR", "Failed to requeue messages", str(e))


@router.get("/worker/stats")
def get_worker_stats(current=Depends(get_current_user)):
    """Get background worker statistics"""
    try:
        worker = get_notification_worker()
        stats = worker.get_stats()
        return ok("Worker statistics retrieved", stats)
        
    except Exception as e:
        return bad(500, "WORKER_ERROR", "Failed to retrieve worker statistics", str(e))


@router.post("/worker/stop")
def stop_worker(current=Depends(get_current_user)):
    """Stop the background worker (admin only)"""
    try:
        worker = get_notification_worker()
        worker.stop()
        return ok("Worker stop signal sent", {
            "message": "Background worker will stop after current batch"
        })
        
    except Exception as e:
        return bad(500, "WORKER_ERROR", "Failed to stop worker", str(e))


@router.get("/health")
def sqs_health_check():
    """Health check for SQS service"""
    if not notification_service:
        return bad(503, "SERVICE_UNAVAILABLE", "SQS service not initialized")
    
    try:
        if not notification_service.enabled:
            return ok("SQS health check", {
                "status": "disabled",
                "message": "SQS notifications are disabled"
            })
        
        # Test queue connectivity
        stats = notification_service.get_queue_stats()
        
        return ok("SQS health check", {
            "status": "healthy",
            "queues_accessible": stats.get("status") == "enabled",
            "notification_queue_exists": stats.get("notification_queue") is not None,
            "dlq_exists": stats.get("dead_letter_queue") is not None
        })
        
    except Exception as e:
        return bad(500, "HEALTH_CHECK_ERROR", "SQS health check failed", str(e))


@router.get("/queues")
def list_queues(current=Depends(get_current_user)):
    """List all SQS queues with notification prefix"""
    if not notification_service:
        return bad(503, "SERVICE_UNAVAILABLE", "SQS service not initialized")
    
    try:
        queues = notification_service.sqs_client.list_queues(prefix="notification")
        
        queue_details = []
        for queue_name in queues:
            stats = notification_service.sqs_client.get_queue_stats(queue_name)
            if stats:
                queue_details.append({
                    "name": queue_name,
                    "visible_messages": stats.visible_messages,
                    "in_flight_messages": stats.in_flight_messages,
                    "created_timestamp": stats.created_timestamp.isoformat() if stats.created_timestamp else None
                })
        
        return ok("Queue list retrieved", {
            "total_queues": len(queue_details),
            "queues": queue_details
        })
        
    except Exception as e:
        return bad(500, "QUEUE_LIST_ERROR", "Failed to list queues", str(e))


@router.delete("/purge/{queue_name}")
def purge_queue(queue_name: str, current=Depends(get_current_user)):
    """Purge all messages from a queue (use with extreme caution)"""
    if not notification_service:
        return bad(503, "SERVICE_UNAVAILABLE", "SQS service not initialized")
    
    # Safety check - only allow purging notification queues
    allowed_queues = [notification_service.notification_queue, notification_service.dlq_queue]
    if queue_name not in allowed_queues:
        return bad(403, "FORBIDDEN", f"Cannot purge queue: {queue_name}")
    
    try:
        success = notification_service.sqs_client.purge_queue(queue_name)
        
        if success:
            return ok("Queue purged successfully", {
                "queue_name": queue_name,
                "purged": True,
                "warning": "All messages in the queue have been permanently deleted"
            })
        else:
            return bad(500, "PURGE_ERROR", f"Failed to purge queue: {queue_name}")
            
    except Exception as e:
        return bad(500, "PURGE_ERROR", "Failed to purge queue", str(e))