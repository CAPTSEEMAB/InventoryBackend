"""
Product notification service for ALL users
"""

import os
import boto3
from pathlib import Path
from dotenv import load_dotenv
from .sns_client import SNSClient

# Load environment variables  
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)


class ProductNotificationService:
    """Service for sending product notifications to ALL registered users with auto-subscription"""
    
    def __init__(self):
        self.sns_client = SNSClient()
        self.enabled = os.getenv('SNS_ENABLE_NOTIFICATIONS', 'true').lower() == 'true'
        
        # Initialize Cognito client to get all users
        self.cognito_client = boto3.client(
            'cognito-idp',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_COGNITO_REGION', 'us-east-1')
        )
        self.user_pool_id = os.getenv('AWS_COGNITO_USER_POOL_ID')
        
        
        # Auto-subscribe all existing users on initialization
        if self.enabled:
            self._auto_subscribe_all_users()
    
    def get_all_user_emails(self) -> list:
        """Get all registered user emails from Cognito"""
        try:
            emails = []
            paginator = self.cognito_client.get_paginator('list_users')
            
            for page in paginator.paginate(UserPoolId=self.user_pool_id):
                for user in page.get('Users', []):
                    # Get email from user attributes
                    for attr in user.get('Attributes', []):
                        if attr['Name'] == 'email':
                            emails.append(attr['Value'])
                            break
            
            return emails
            
        except Exception as e:
            return []
    
    def subscribe_user(self, email: str) -> bool:
        """Subscribe a single user to product notifications"""
        try:
            topic_arn = self.sns_client._get_or_create_topic("product-notifications")
            if not topic_arn:
                return False
            
            # Check if already subscribed
            subs_response = self.sns_client.sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
            existing_emails = [sub['Endpoint'] for sub in subs_response.get('Subscriptions', [])]
            
            if email not in existing_emails:
                # Subscribe the email
                self.sns_client.sns_client.subscribe(
                    TopicArn=topic_arn,
                    Protocol='email',
                    Endpoint=email
                )
                return True
            else:
                return True
                
        except Exception as e:
            return False
    
    def _auto_subscribe_all_users(self) -> bool:
        """Private method to auto-subscribe all users during service initialization"""
        try:
            return self.subscribe_all_users()
        except Exception as e:
            return False
    
    def subscribe_all_users(self) -> bool:
        """Subscribe all registered users to product notifications"""
        try:
            emails = self.get_all_user_emails()
            if not emails:
                return False
            
            topic_arn = self.sns_client._get_or_create_topic("product-notifications")
            if not topic_arn:
                return False
            
            subscribed_count = 0
            for email in emails:
                try:
                    # Check if already subscribed by getting current subscriptions
                    subs_response = self.sns_client.sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
                    existing_emails = [sub['Endpoint'] for sub in subs_response.get('Subscriptions', [])]
                    
                    if email not in existing_emails:
                        # Subscribe the email
                        self.sns_client.sns_client.subscribe(
                            TopicArn=topic_arn,
                            Protocol='email',
                            Endpoint=email
                        )
                        subscribed_count += 1
                        
                except Exception as e:
                    pass
            
            return True
            
        except Exception as e:
            return False
    
    def notify_product_created(self, product_data: dict) -> bool:
        """Send notification to ALL registered users when a new product is created"""
        if not self.enabled:
            return True
        
        try:
            # First, ensure all users are subscribed
            self.subscribe_all_users()
            
            # Get count of all users for the message
            all_emails = self.get_all_user_emails()
            user_count = len(all_emails)
            
            subject = f"🆕 New Product Alert: {product_data.get('name', 'Unknown')}"
            message = f"""
🎉 NEW PRODUCT ADDED TO INVENTORY!

📱 Product Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {product_data.get('name', 'N/A')}
• SKU: {product_data.get('sku', 'N/A')}  
• Price: ${product_data.get('price', 'N/A')}
• Category: {product_data.get('category', 'N/A')}
• Stock: {product_data.get('in_stock', 'N/A')} units
• Supplier: {product_data.get('supplier', 'N/A')}
• Description: {product_data.get('description', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Added: {product_data.get('created_at', 'N/A')}
👥 Notified: All {user_count} registered users

🛒 This notification was sent automatically to all users in the inventory system.
            """.strip()
            
            return self.sns_client.publish_message(
                topic="product-notifications",
                message=message,
                subject=subject
            )
            
        except Exception as e:
            return False