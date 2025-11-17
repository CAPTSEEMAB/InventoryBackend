"""
DynamoDB utility functions for the Inventory API
Provides CRUD operations and query helpers for DynamoDB tables
"""

import boto3
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

class DynamoDBClient:
    def __init__(self):
        """Initialize DynamoDB client with AWS credentials from environment"""
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not self.aws_access_key or not self.aws_secret_key:
            raise ValueError("AWS credentials not found in environment variables")
        
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )
        
        self.user_profiles = self.dynamodb.Table('user_profiles')
        self.inventory_products = self.dynamodb.Table('inventory_products')
    
    def _convert_decimals(self, obj):
        """Convert DynamoDB Decimal types to float/int"""
        if isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        else:
            return obj
    
    def _prepare_item(self, item: Dict) -> Dict:
        """Prepare item for DynamoDB by converting float to Decimal"""
        if isinstance(item, dict):
            return {k: self._prepare_item(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [self._prepare_item(i) for i in item]
        elif isinstance(item, float):
            return Decimal(str(item))
        else:
            return item
    

    
    def create_user_profile(self, email: str, name: str, password_hash: str = None) -> Dict:
        """Create a new user profile"""
        user_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        item = {
            'id': user_id,
            'email': email,
            'name': name,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        if password_hash:
            item['password_hash'] = password_hash
        
        try:
            self.user_profiles.put_item(
                Item=self._prepare_item(item),
                ConditionExpression='attribute_not_exists(id)'
            )
            return self._convert_decimals(item)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("User with this ID already exists")
            raise e
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user profile by ID"""
        try:
            response = self.user_profiles.get_item(Key={'id': user_id})
            return self._convert_decimals(response.get('Item'))
        except ClientError:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user profile by email using GSI"""
        try:
            response = self.user_profiles.query(
                IndexName='email-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
            )
            items = response.get('Items', [])
            return self._convert_decimals(items[0]) if items else None
        except ClientError:
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Optional[Dict]:
        """Update user profile"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        updates['updated_at'] = timestamp
        
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for key, value in updates.items():
            safe_key = f"#{key}"
            value_key = f":{key}"
            expr_attr_names[safe_key] = key
            expr_attr_values[value_key] = self._prepare_item(value)
            update_expr += f"{safe_key} = {value_key}, "
        
        update_expr = update_expr.rstrip(", ")
        
        try:
            response = self.user_profiles.update_item(
                Key={'id': user_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            return self._convert_decimals(response.get('Attributes'))
        except ClientError:
            return None
    
    def delete_user_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        try:
            self.user_profiles.delete_item(Key={'id': user_id})
            return True
        except ClientError:
            return False
    

    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new inventory product"""
        product_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        item = {
            'id': product_id,
            'created_at': timestamp,
            'updated_at': timestamp,
            **product_data
        }
        
        try:
            self.inventory_products.put_item(
                Item=self._prepare_item(item),
                ConditionExpression='attribute_not_exists(id)'
            )
            return self._convert_decimals(item)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("Product with this ID already exists")
            raise e
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get product by ID"""
        try:
            response = self.inventory_products.get_item(Key={'id': product_id})
            return self._convert_decimals(response.get('Item'))
        except ClientError:
            return None
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get product by SKU using GSI"""
        try:
            response = self.inventory_products.query(
                IndexName='sku-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('sku').eq(sku)
            )
            items = response.get('Items', [])
            return self._convert_decimals(items[0]) if items else None
        except ClientError:
            return None
    
    def get_products_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """Get products by category using GSI"""
        try:
            response = self.inventory_products.query(
                IndexName='category-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('category').eq(category),
                Limit=limit
            )
            return self._convert_decimals(response.get('Items', []))
        except ClientError:
            return []
    
    def get_all_products(self, limit: int = 100) -> List[Dict]:
        """Get all products with optional limit"""
        try:
            response = self.inventory_products.scan(Limit=limit)
            return self._convert_decimals(response.get('Items', []))
        except ClientError:
            return []
    
    def update_product(self, product_id: str, updates: Dict) -> Optional[Dict]:
        """Update product"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        updates['updated_at'] = timestamp
        
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for key, value in updates.items():
            safe_key = f"#{key}"
            value_key = f":{key}"
            expr_attr_names[safe_key] = key
            expr_attr_values[value_key] = self._prepare_item(value)
            update_expr += f"{safe_key} = {value_key}, "
        
        update_expr = update_expr.rstrip(", ")
        
        try:
            response = self.inventory_products.update_item(
                Key={'id': product_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            return self._convert_decimals(response.get('Attributes'))
        except ClientError:
            return None
    
    def delete_product(self, product_id: str) -> bool:
        """Delete product"""
        try:
            self.inventory_products.delete_item(Key={'id': product_id})
            return True
        except ClientError:
            return False
    
    def add_stock_movement(self, product_id: str, movement_type: str, quantity: int, date: str = None) -> bool:
        """Add stock movement to product"""
        if not date:
            date = datetime.utcnow().date().isoformat()
        
        movement = {
            'movement_date': date,
            'type': movement_type,
            'quantity': quantity
        }
        
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return False
            
            movements = product.get('movements', [])
            movements.append(movement)
            
            current_stock = product.get('in_stock', 0)
            if movement_type == 'IN':
                new_stock = current_stock + quantity
            else:
                new_stock = max(0, current_stock - quantity)
            
            self.update_product(product_id, {
                'movements': movements,
                'in_stock': new_stock
            })
            
            return True
        except ClientError:
            return False
    

    
    def health_check(self) -> Dict:
        """Check database connection and table status"""
        try:
            user_response = self.user_profiles.scan(Limit=1)
            user_count = user_response['Count']
            
            product_response = self.inventory_products.scan(Limit=1)
            product_count = product_response['Count']
            
            return {
                'status': 'healthy',
                'user_profiles': f"{user_count} items accessible",
                'inventory_products': f"{product_count} items accessible",
                'region': self.aws_region
            }
        except ClientError as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

db_client = None

def get_db_client() -> DynamoDBClient:
    """Get or create DynamoDB client instance"""
    global db_client
    if db_client is None:
        db_client = DynamoDBClient()
    return db_client