# AWS Setup Guide for Inventory API

## Prerequisites
- AWS Account
- AWS CLI installed and configured (`aws configure`)
- Python environment with boto3 installed

## Option 1: Automated Setup (Recommended)

Run the setup script:
```bash
python setup_aws_resources.py
```

This will automatically:
- Create DynamoDB tables
- Set up Cognito User Pool
- Update your .env file with the resource IDs

## Option 2: Manual Setup via AWS Console

### 1. Set up DynamoDB Tables

#### Create `inventory_products` table:
1. Go to AWS Console → DynamoDB → Tables → Create table
2. Table name: `inventory_products`
3. Partition key: `id` (String)
4. Settings: Use default settings
5. Billing mode: On-demand
6. Click "Create table"

#### Create `user_profiles` table:
1. Go to AWS Console → DynamoDB → Tables → Create table
2. Table name: `user_profiles`
3. Partition key: `id` (String)
4. Settings: Use default settings
5. Billing mode: On-demand
6. Click "Create table"

### 2. Set up Cognito User Pool

1. Go to AWS Console → Cognito → User pools → Create user pool

2. **Step 1: Authentication providers**
   - Provider types: Cognito user pool
   - Cognito user pool sign-in options: Email

3. **Step 2: Security requirements**
   - Password policy: Choose your preferred settings
   - Multi-factor authentication: No MFA (for development)

4. **Step 3: Sign-up experience**
   - Self-service sign-up: Enable
   - Attribute verification and user account confirmation: Send email verification messages
   - Required attributes: Email
   - Custom attributes: None

5. **Step 4: Message delivery**
   - Email provider: Send email with Cognito
   - FROM email address: Use default

6. **Step 5: Integrate your app**
   - User pool name: `inventory-api-user-pool`
   - App client name: `inventory-api-client`
   - Client secret: Don't generate (uncheck)
   - Authentication flows: ALLOW_USER_PASSWORD_AUTH, ALLOW_REFRESH_TOKEN_AUTH

7. Review and create

8. **Note down the following from the created User Pool:**
   - User Pool ID (from General settings)
   - App Client ID (from App integration → App clients)

### 3. Get AWS Credentials

1. Go to AWS Console → IAM → Users → Your user → Security credentials
2. Create access key if you don't have one
3. Note down:
   - Access Key ID
   - Secret Access Key

### 4. Update .env file

Replace the placeholder values in your `.env` file:

```bash
# Replace these with your actual values
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1  # or your preferred region
COGNITO_USER_POOL_ID=us-east-1_...
COGNITO_CLIENT_ID=...
```

## Testing the Setup

1. Restart your FastAPI application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Go to http://localhost:8000/api/docs

3. Test user registration:
   ```bash
   curl -X POST "http://localhost:8000/api/auth/signup" \
   -H "Content-Type: application/json" \
   -d '{
     "email": "test@example.com",
     "password": "TestPassword123"
   }'
   ```

4. Check your email for verification code and confirm the user

5. Test login:
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \
   -H "Content-Type: application/json" \
   -d '{
     "email": "test@example.com",
     "password": "TestPassword123"
   }'
   ```

## Troubleshooting

### Common Issues:

1. **"Invalid AWS credentials"**
   - Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct
   - Check if the IAM user has necessary permissions (DynamoDB, Cognito)

2. **"Table not found"**
   - Ensure tables are created in the same AWS region as specified in .env
   - Check table names match exactly: `inventory_products`, `user_profiles`

3. **"User pool not found"**
   - Verify COGNITO_USER_POOL_ID is correct
   - Ensure User Pool is in the same region as other resources

4. **"Invalid client id"**
   - Verify COGNITO_CLIENT_ID is correct
   - Ensure the client doesn't have a secret (should be a public client)

### Required IAM Permissions:

Your AWS user needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:*",
                "cognito-idp:*"
            ],
            "Resource": "*"
        }
    ]
}
```