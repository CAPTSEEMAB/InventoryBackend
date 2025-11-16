#!/bin/bash

# Interactive AWS Setup Script for Inventory API
# This script guides you through the complete setup process

clear
echo "🎯 Interactive AWS Setup for Inventory API"
echo "=========================================="
echo ""

# Check if we're in virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment is active: $(basename $VIRTUAL_ENV)"
else
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo "✅ Virtual environment activated: $(basename $VIRTUAL_ENV)"
    else
        echo "❌ Failed to activate virtual environment. Please check if venv exists."
        exit 1
    fi
fi

echo ""
echo "🔐 AWS Credentials Setup"
echo "========================"
echo ""
echo "You need AWS credentials to proceed. If you don't have them yet:"
echo "1. Go to AWS Console → IAM → Users → Create user"
echo "2. Attach the policy from 'iam-policy.json'"
echo "3. Create access keys"
echo ""

# Check current AWS configuration
if aws configure list &>/dev/null; then
    echo "📋 Current AWS configuration:"
    aws configure list
    echo ""
    read -p "Do you want to update your AWS credentials? (y/N): " update_creds
else
    update_creds="y"
    echo "⚠️  No AWS configuration found."
fi

if [[ "$update_creds" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please enter your AWS credentials:"
    read -p "AWS Access Key ID: " aws_access_key
    read -s -p "AWS Secret Access Key: " aws_secret_key
    echo ""
    read -p "AWS Region (default: us-east-1): " aws_region
    aws_region=${aws_region:-us-east-1}
    
    # Configure AWS CLI
    aws configure set aws_access_key_id "$aws_access_key"
    aws configure set aws_secret_access_key "$aws_secret_key"
    aws configure set region "$aws_region"
    aws configure set output json
    
    echo "✅ AWS credentials configured"
fi

echo ""
echo "🔍 Testing AWS Connection..."
echo "============================"

# Test AWS credentials
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS credentials are valid!"
    identity=$(aws sts get-caller-identity)
    echo "$identity"
else
    echo "❌ AWS credentials are invalid or AWS CLI is not configured properly."
    echo ""
    echo "Please ensure:"
    echo "1. Your AWS credentials are correct"
    echo "2. Your AWS user has the necessary permissions (see iam-policy.json)"
    echo "3. Your AWS account is active and has no billing issues"
    exit 1
fi

echo ""
echo "🏗️  Creating AWS Resources..."
echo "============================="

# Run the Python setup script
echo "Running Python setup script..."
python setup_aws_resources.py

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ AWS resources setup completed!"
else
    echo ""
    echo "❌ AWS resources setup failed. Please check the errors above."
    exit 1
fi

echo ""
echo "📝 Updating .env file..."
echo "======================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Show current .env content (masked)
echo "Current .env file (credentials masked):"
echo "======================================"
sed 's/\(AWS_ACCESS_KEY_ID=\).*/\1***MASKED***/g; s/\(AWS_SECRET_ACCESS_KEY=\).*/\1***MASKED***/g' .env
echo ""

echo "⚠️  Please manually update the following in your .env file:"
echo "1. AWS_ACCESS_KEY_ID (replace with your actual access key)"
echo "2. AWS_SECRET_ACCESS_KEY (replace with your actual secret key)"
echo "3. Verify COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID were updated by the script"

echo ""
echo "🧪 Testing Application..."
echo "========================"

echo "Testing Python imports..."
python -c "
import boto3
import sys
print('✅ All Python packages imported successfully')

try:
    # Test AWS connection
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print('✅ AWS connection working')
    
    # Test DynamoDB
    dynamodb = boto3.client('dynamodb')
    tables = dynamodb.list_tables()
    required_tables = ['inventory_products', 'user_profiles']
    existing_tables = tables['TableNames']
    
    for table in required_tables:
        if table in existing_tables:
            print(f'✅ DynamoDB table {table} exists')
        else:
            print(f'❌ DynamoDB table {table} missing')
    
    # Test Cognito
    cognito = boto3.client('cognito-idp')
    pools = cognito.list_user_pools(MaxResults=10)
    print(f'✅ Cognito accessible, {len(pools[\"UserPools\"])} user pools found')
    
except Exception as e:
    print(f'❌ Error during testing: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup Completed Successfully!"
    echo "==============================="
    echo ""
    echo "Next steps:"
    echo "1. Update your .env file with real AWS credentials (see above)"
    echo "2. Restart your FastAPI application:"
    echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo "3. Test the API at: http://localhost:8000/api/docs"
    echo "4. Try creating a user with: POST /api/auth/signup"
    echo ""
    echo "📚 For detailed instructions, see: COMPLETE_AWS_SETUP_GUIDE.md"
else
    echo ""
    echo "❌ Setup testing failed. Please check the errors above."
fi