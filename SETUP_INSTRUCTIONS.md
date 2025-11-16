# AWS Setup Instructions

## You're right about the virtual environment issue!

The problem was that we were opening new terminals without activating the virtual environment. Now I can see that the virtual environment is properly activated (notice the `(venv)` prefix in the terminal).

## Current Status:
✅ Virtual environment is active
✅ Required packages are installed in venv
❌ AWS credentials need to be configured properly

## Next Steps:

### 1. Configure AWS Credentials

You need to get actual AWS credentials from your AWS account:

1. **Go to AWS Console** → IAM → Users → Your user → Security credentials
2. **Create Access Key** (if you don't have one)
3. **Note down:**
   - Access Key ID (starts with AKIA...)
   - Secret Access Key

### 2. Configure AWS CLI with real credentials:

```bash
# Run these commands in the terminal (the venv is already active):
aws configure set aws_access_key_id YOUR_ACTUAL_ACCESS_KEY_ID
aws configure set aws_secret_access_key YOUR_ACTUAL_SECRET_ACCESS_KEY
aws configure set region us-east-1
```

### 3. Test the configuration:

```bash
aws sts get-caller-identity
```

This should return your AWS account details if configured correctly.

### 4. Run the setup script:

```bash
python setup_aws_resources.py
```

## Alternative: Use Environment Variables

Instead of configuring AWS CLI globally, you can also set the credentials in your `.env` file and the application will use them directly.

### Current .env file needs:
```bash
AWS_ACCESS_KEY_ID=your_actual_access_key_here
AWS_SECRET_ACCESS_KEY=your_actual_secret_key_here  
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=will_be_generated
COGNITO_CLIENT_ID=will_be_generated
```

## Important Notes:

1. **Never commit real AWS credentials to git**
2. **Use IAM users with minimal required permissions**
3. **The virtual environment is now working correctly** - packages are installed in the right place
4. **All terminal commands should show `(venv)` prefix** indicating the virtual environment is active

## Required IAM Permissions:

Your AWS user needs these permissions:
- DynamoDB: CreateTable, DescribeTable, ListTables
- Cognito: CreateUserPool, CreateUserPoolClient
- STS: GetCallerIdentity (for testing)

Would you like me to create a minimal IAM policy for these permissions?