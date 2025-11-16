#!/usr/bin/env python3
"""
Quick AWS Credentials and Setup Checker
Run this to verify your AWS setup is working correctly
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pathlib import Path
from dotenv import load_dotenv

def check_env_file():
    """Check .env file configuration"""
    print("🔍 Checking .env file...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    load_dotenv()
    
    required_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY", 
        "AWS_REGION",
        "COGNITO_USER_POOL_ID",
        "COGNITO_CLIENT_ID"
    ]
    
    missing_vars = []
    placeholder_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif value in ["aws_access_key_id", "aws_secret_access_key", "cognito_user_pool_id", "cognito_client_id", "your_actual_access_key_here", "your_actual_secret_key_here"]:
            placeholder_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    if placeholder_vars:
        print(f"⚠️  Placeholder values found in: {', '.join(placeholder_vars)}")
        print("   Please update these with your actual AWS credentials")
        return False
    
    print("✅ .env file configuration looks good")
    return True

def check_aws_credentials():
    """Check AWS credentials"""
    print("\n🔐 Checking AWS credentials...")
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ AWS credentials are valid!")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Run: aws configure")
        return False
    except ClientError as e:
        print(f"❌ AWS credentials error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def check_dynamodb():
    """Check DynamoDB tables"""
    print("\n📊 Checking DynamoDB tables...")
    
    try:
        dynamodb = boto3.client('dynamodb')
        tables = dynamodb.list_tables()
        existing_tables = tables['TableNames']
        
        required_tables = ['inventory_products', 'user_profiles']
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
                
                # Check table status
                response = dynamodb.describe_table(TableName=table)
                status = response['Table']['TableStatus']
                print(f"   Status: {status}")
            else:
                print(f"❌ Table '{table}' not found")
                return False
        
        return True
        
    except ClientError as e:
        print(f"❌ DynamoDB error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def check_cognito():
    """Check Cognito User Pool"""
    print("\n👤 Checking Cognito User Pool...")
    
    try:
        load_dotenv()
        user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        client_id = os.getenv('COGNITO_CLIENT_ID')
        
        if not user_pool_id or not client_id:
            print("❌ Cognito IDs not found in .env file")
            return False
        
        cognito = boto3.client('cognito-idp')
        
        # Check User Pool
        try:
            pool_response = cognito.describe_user_pool(UserPoolId=user_pool_id)
            pool_name = pool_response['UserPool']['Name']
            print(f"✅ User Pool '{pool_name}' found")
            print(f"   ID: {user_pool_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ User Pool '{user_pool_id}' not found")
                return False
            raise
        
        # Check App Client
        try:
            client_response = cognito.describe_user_pool_client(
                UserPoolId=user_pool_id,
                ClientId=client_id
            )
            client_name = client_response['UserPoolClient']['ClientName']
            print(f"✅ App Client '{client_name}' found")
            print(f"   ID: {client_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ App Client '{client_id}' not found")
                return False
            raise
        
        return True
        
    except ClientError as e:
        print(f"❌ Cognito error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main checking function"""
    print("🎯 AWS Setup Verification")
    print("=" * 30)
    
    checks = [
        ("Environment Configuration", check_env_file),
        ("AWS Credentials", check_aws_credentials),
        ("DynamoDB Tables", check_dynamodb),
        ("Cognito User Pool", check_cognito)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except KeyboardInterrupt:
            print("\n\n⚠️  Check interrupted by user")
            return
        except Exception as e:
            print(f"❌ Error during {check_name}: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 30)
    if all_passed:
        print("🎉 All checks passed! Your AWS setup is ready.")
        print("\nNext steps:")
        print("1. Start your FastAPI app: uvicorn app.main:app --reload")
        print("2. Test the API at: http://localhost:8000/api/docs")
        print("3. Try user signup: POST /api/auth/signup")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nFor help:")
        print("1. Check COMPLETE_AWS_SETUP_GUIDE.md")
        print("2. Run interactive_setup.sh")

if __name__ == "__main__":
    main()