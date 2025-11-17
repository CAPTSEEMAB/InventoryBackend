"""
Simple interface for SNS message publishing
"""

from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    """Abstract base class for notification providers"""
    
    @abstractmethod
    def publish_message(self, topic: str, message: str, subject: str = None) -> bool:
        """Publish a message to a topic"""
        pass