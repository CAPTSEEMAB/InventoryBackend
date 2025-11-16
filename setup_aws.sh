#!/bin/bash
# Script to set up AWS credentials and resources for Inventory API

echo "🎯 AWS Setup Script for Inventory API"
echo "======================================"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Check Python and pip
echo "🐍 Python version: $(python --version)"
echo "📦 Using pip from: $(which pip)"

# Configure AWS CLI
echo ""
echo "🔧 AWS CLI Configuration"
echo "========================"

read -p "Enter your AWS Access Key ID: " aws_access_key
read -s -p "Enter your AWS Secret Access Key: " aws_secret_key
echo ""
read -p "Enter your AWS Region (e.g., us-east-1): " aws_region

# Configure AWS CLI
aws configure set aws_access_key_id "$aws_access_key"
aws configure set aws_secret_access_key "$aws_secret_key" 
aws configure set region "$aws_region"

# Verify AWS configuration
echo ""
echo "🔍 Verifying AWS credentials..."
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS credentials are valid"
    aws sts get-caller-identity
else
    echo "❌ AWS credentials are invalid. Please check your keys."
    exit 1
fi

# Run the Python setup script
echo ""
echo "🚀 Running AWS resources setup..."
python setup_aws_resources.py

echo ""
echo "✅ Setup completed! Check the output above for any errors."
echo "📝 Next: Update your .env file with the generated IDs and restart your FastAPI app."