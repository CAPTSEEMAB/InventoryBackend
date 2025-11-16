#!/usr/bin/env python3
"""
AWS Resources Setup Script for Inventory API
This script sets up DynamoDB tables and Cognito User Pool for the application.
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

def setup_dynamodb_tables():
    """Create required DynamoDB tables"""
    print("🚀 Setting up DynamoDB tables...")
    
    try:
        # Create DynamoDB client
        dynamodb = boto3.client('dynamodb')
        
        # Table configurations
        tables_config = [
            {
                'TableName': 'inventory_products',
                'KeySchema': [
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    }
                ],
                'AttributeDefinitions': [
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    }
                ],
                'BillingMode': 'PAY_PER_REQUEST'
            },
            {
                'TableName': 'user_profiles',
                'KeySchema': [
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    }
                ],
                'AttributeDefinitions': [
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    }
                ],
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ]
        
        # Create tables
        for table_config in tables_config:
            table_name = table_config['TableName']
            
            # Check if table already exists
            try:
                response = dynamodb.describe_table(TableName=table_name)
                print(f"✅ Table '{table_name}' already exists")
                continue
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Table doesn't exist, create it
                    pass
                else:
                    raise e
            
            # Create the table
            print(f"📋 Creating table '{table_name}'...")
            response = dynamodb.create_table(**table_config)
            
            # Wait for table to be created
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"✅ Table '{table_name}' created successfully")
            
    except Exception as e:
        print(f"❌ Error setting up DynamoDB tables: {str(e)}")
        return False
    
    return True

def setup_cognito_user_pool():
    """Create Cognito User Pool"""
    print("🚀 Setting up Cognito User Pool...")
    
    try:
        # Create Cognito Identity Provider client
        cognito = boto3.client('cognito-idp')
        
        # User Pool configuration
        user_pool_config = {
            'PoolName': 'inventory-api-user-pool',
            'Policies': {
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            },
            'AutoVerifiedAttributes': ['email'],
            'AliasAttributes': ['email'],
            'UsernameAttributes': ['email'],
            'VerificationMessageTemplate': {
                'DefaultEmailOption': 'CONFIRM_WITH_CODE',
                'EmailSubject': 'Verify your email for Inventory API',
                'EmailMessage': 'Your verification code is {####}'
            },
            'EmailConfiguration': {
                'EmailSendingAccount': 'COGNITO_DEFAULT'
            },
            'AdminCreateUserConfig': {
                'AllowAdminCreateUserOnly': False,
                'InviteMessageTemplate': {
                    'EmailSubject': 'Welcome to Inventory API',
                    'EmailMessage': 'Your username is {username} and temporary password is {####}'
                }
            }
        }
        
        # Create User Pool
        print("📋 Creating Cognito User Pool...")
        response = cognito.create_user_pool(**user_pool_config)
        user_pool_id = response['UserPool']['Id']
        print(f"✅ User Pool created with ID: {user_pool_id}")
        
        # Create User Pool Client
        client_config = {
            'UserPoolId': user_pool_id,
            'ClientName': 'inventory-api-client',
            'GenerateSecret': False,  # No secret for web/mobile apps
            'RefreshTokenValidity': 30,
            'AccessTokenValidity': 24,
            'IdTokenValidity': 24,
            'TokenValidityUnits': {
                'AccessToken': 'hours',
                'IdToken': 'hours',
                'RefreshToken': 'days'
            },
            'ExplicitAuthFlows': [
                'ADMIN_NO_SRP_AUTH',
                'USER_PASSWORD_AUTH',
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH'
            ],
            'SupportedIdentityProviders': ['COGNITO'],
            'CallbackURLs': ['http://localhost:8000'],
            'LogoutURLs': ['http://localhost:8000'],
            'AllowedOAuthFlows': ['implicit'],
            'AllowedOAuthScopes': ['openid', 'email', 'profile'],
            'AllowedOAuthFlowsUserPoolClient': True
        }
        
        print("📋 Creating User Pool Client...")
        client_response = cognito.create_user_pool_client(**client_config)
        client_id = client_response['UserPoolClient']['ClientId']
        print(f"✅ User Pool Client created with ID: {client_id}")
        
        return user_pool_id, client_id
        
    except Exception as e:
        print(f"❌ Error setting up Cognito User Pool: {str(e)}")
        return None, None

def update_env_file(user_pool_id=None, client_id=None):
    """Update .env file with AWS resource IDs"""
    print("🚀 Updating .env file...")
    
    env_file = '.env'
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update the relevant lines
    updated_lines = []
    for line in lines:
        if line.startswith('AWS_ACCESS_KEY_ID=') and 'aws_access_key_id' in line:
            updated_lines.append('AWS_ACCESS_KEY_ID=your_actual_access_key_here\n')
            print("⚠️  Please update AWS_ACCESS_KEY_ID with your actual access key")
        elif line.startswith('AWS_SECRET_ACCESS_KEY=') and 'aws_secret_access_key' in line:
            updated_lines.append('AWS_SECRET_ACCESS_KEY=your_actual_secret_key_here\n')
            print("⚠️  Please update AWS_SECRET_ACCESS_KEY with your actual secret key")
        elif line.startswith('COGNITO_USER_POOL_ID=') and user_pool_id:
            updated_lines.append(f'COGNITO_USER_POOL_ID={user_pool_id}\n')
            print(f"✅ Updated COGNITO_USER_POOL_ID: {user_pool_id}")
        elif line.startswith('COGNITO_CLIENT_ID=') and client_id:
            updated_lines.append(f'COGNITO_CLIENT_ID={client_id}\n')
            print(f"✅ Updated COGNITO_CLIENT_ID: {client_id}")
        else:
            updated_lines.append(line)
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ .env file updated")

def main():
    """Main setup function"""
    print("🎯 AWS Resources Setup for Inventory API")
    print("=" * 50)
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials valid for account: {identity['Account']}")
        print(f"   ARN: {identity['Arn']}")
        print()
    except Exception as e:
        print(f"❌ AWS credentials not configured properly: {str(e)}")
        print("   Please run: aws configure")
        return
    
    # Setup DynamoDB tables
    if setup_dynamodb_tables():
        print("✅ DynamoDB setup completed\n")
    else:
        print("❌ DynamoDB setup failed\n")
        return
    
    # Setup Cognito User Pool
    user_pool_id, client_id = setup_cognito_user_pool()
    if user_pool_id and client_id:
        print("✅ Cognito setup completed\n")
    else:
        print("❌ Cognito setup failed\n")
        return
    
    # Update .env file
    update_env_file(user_pool_id, client_id)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env")
    print("2. Restart your FastAPI application")
    print("3. Test the /api/auth/signup endpoint")

if __name__ == "__main__":
    main()