# AWS Infrastructure Setup Scripts

This directory contains setup scripts to create all required AWS resources for the Inventory API.

## Scripts Overview

### Individual Service Scripts

1. **`setup_dynamodb.py`** - Creates DynamoDB tables
   - `user_profiles` table with email GSI
   - `inventory_products` table with category and SKU GSIs
   - Detects existing tables automatically

2. **`setup_cognito.py`** - Creates Cognito User Pool
   - User Pool with email authentication
   - App Client for API access
   - Updates `.env` file with pool configuration
   - Detects existing pools automatically

3. **`setup_sns.py`** - Creates SNS notification system
   - `product-notifications` topic
   - Filter policies for different notification types
   - Updates `.env` file with SNS configuration
   - Detects existing topics automatically

4. **`setup_s3.py`** - Creates S3 bucket for file storage
   - Secure bucket with encryption and versioning
   - CORS configuration for web access
   - Lifecycle policies for cost optimization
   - Updates `.env` file with bucket name
   - Detects existing buckets automatically

### Master Setup Script

**`setup_aws_infrastructure.py`** - Runs all setup scripts in correct order
- Checks prerequisites (AWS credentials)
- Runs individual scripts sequentially
- Creates deployment summary
- Handles errors gracefully

## Usage

### Prerequisites

1. **AWS Credentials**: Create a `.env` file with:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   ```

2. **Python Dependencies**: Install required packages:
   ```bash
   pip install boto3 python-dotenv
   ```

3. **IAM Permissions**: Ensure your AWS user has permissions for:
   - DynamoDB: `CreateTable`, `DescribeTable`
   - Cognito: `CreateUserPool`, `CreateUserPoolClient`
   - SNS: `CreateTopic`, `ListTopics`
   - S3: `CreateBucket`, `PutBucketPolicy`, etc.

### Running Scripts

#### Option 1: Master Setup (Recommended)
```bash
python3 scripts/setup_aws_infrastructure.py
```

#### Option 2: Individual Scripts
```bash
python3 scripts/setup_dynamodb.py
python3 scripts/setup_cognito.py  
python3 scripts/setup_sns.py
python3 scripts/setup_s3.py
```

## Features

### Smart Detection
- **Existing Resources**: All scripts detect existing AWS resources
- **No Duplicates**: Won't create duplicate resources if they already exist
- **Configuration Reuse**: Uses existing resource IDs from `.env` file

### Error Handling
- **Prerequisites Check**: Validates AWS credentials before starting
- **Graceful Failures**: Continues with other resources if one fails
- **Clear Messages**: Detailed success/failure reporting

### Configuration Management
- **Auto-Update**: Scripts automatically update `.env` file
- **Validation**: Verifies resources are created and accessible
- **Summary**: Generates deployment summary document

## Output Files

After successful setup, you'll have:
- **Updated `.env`**: With all AWS resource configurations
- **`DEPLOYMENT_SUMMARY.md`**: Complete overview of created resources

## Troubleshooting

### Common Issues

1. **Missing Permissions**: Ensure IAM user has required permissions
2. **Region Issues**: Some resources are region-specific
3. **Existing Resources**: Scripts handle existing resources gracefully

### Verification

Each script includes verification steps:
- Tests resource accessibility
- Validates configurations
- Reports any issues

### Manual Cleanup

To remove resources (if needed):
1. **DynamoDB**: Delete tables in AWS Console
2. **Cognito**: Delete User Pool in AWS Console
3. **SNS**: Delete topic in AWS Console
4. **S3**: Empty and delete bucket in AWS Console

## Security Notes

- S3 buckets are created with public access blocked
- Cognito requires email verification
- DynamoDB uses pay-per-request billing (cost-effective)
- SNS topics auto-subscribe registered users

## Next Steps

After running setup:

1. **Start API Server**:
   ```bash
   uvicorn app.main:app --reload --port 3000
   ```

2. **Test in Swagger UI**: http://localhost:3000/api/docs

3. **Create Users**: Use signup endpoint to create accounts

4. **Test Features**: Try product CRUD, file upload, notifications