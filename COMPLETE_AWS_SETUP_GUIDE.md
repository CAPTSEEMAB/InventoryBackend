# Complete AWS Setup Guide for Inventory API

## 🎯 Overview
This guide will help you set up AWS resources for your Inventory API with proper security and minimal permissions.

## 📋 Prerequisites
- AWS Account (free tier is sufficient)
- Email address for Cognito verification

---

## 🔐 Step 1: Create IAM User with Minimal Permissions

### 1.1 Create IAM User
1. **Log into AWS Console** → [IAM Dashboard](https://console.aws.amazon.com/iam/)
2. **Click "Users"** → **"Create user"**
3. **User name**: `inventory-api-user`
4. **Access type**: Select "Programmatic access" 
5. **Click "Next"**

### 1.2 Attach Policy
1. **Select "Attach policies directly"**
2. **Click "Create policy"**
3. **Switch to JSON tab** and paste the content from `iam-policy.json`
4. **Policy name**: `InventoryAPIPolicy`
5. **Click "Create policy"**
6. **Go back to user creation** and attach the policy you just created
7. **Complete user creation**

### 1.3 Get Access Keys
1. **Click on the created user**
2. **Go to "Security credentials" tab**
3. **Click "Create access key"**
4. **Use case**: Select "Application running outside AWS"
5. **Click "Next"** → **"Create access key"**
6. **⚠️ IMPORTANT: Download the CSV file or copy the keys immediately!**
   - Access Key ID (starts with AKIA...)
   - Secret Access Key (long random string)

---

## 🛠️ Step 2: Configure AWS CLI

### 2.1 Set Your Credentials
Run these commands in your terminal (make sure you see `(venv)` prefix):

```bash
# Replace YOUR_ACCESS_KEY_ID with the actual key from Step 1.3
aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID

# Replace YOUR_SECRET_ACCESS_KEY with the actual secret from Step 1.3  
aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY

# Set your preferred region (us-east-1 is recommended for this tutorial)
aws configure set region us-east-1

# Set output format
aws configure set output json
```

### 2.2 Test Configuration
```bash
aws sts get-caller-identity
```
**Expected output:**
```json
{
    "UserId": "AIDACKCEVSQ6C2EXAMPLE",
    "Account": "123456789012", 
    "Arn": "arn:aws:iam::123456789012:user/inventory-api-user"
}
```

---

## 🏗️ Step 3: Create AWS Resources (Two Options)

### Option A: Automated Setup (Recommended)

Run our setup script:
```bash
python setup_aws_resources.py
```

### Option B: Manual Setup via AWS Console

#### 3.1 Create DynamoDB Tables

**Create `inventory_products` table:**
1. **AWS Console** → [DynamoDB](https://console.aws.amazon.com/dynamodb/)
2. **Create table**
3. **Table name**: `inventory_products`
4. **Partition key**: `id` (String)
5. **Table settings**: Default settings
6. **Billing mode**: On-demand
7. **Click "Create table"**

**Create `user_profiles` table:**
1. **Create table**
2. **Table name**: `user_profiles` 
3. **Partition key**: `id` (String)
4. **Table settings**: Default settings
5. **Billing mode**: On-demand
6. **Click "Create table"**

#### 3.2 Create Cognito User Pool

1. **AWS Console** → [Cognito](https://console.aws.amazon.com/cognito/)
2. **Create user pool**

**Step 1: Configure sign-in experience**
- **Provider types**: Cognito user pool
- **User pool sign-in options**: ✅ Email

**Step 2: Configure security requirements**  
- **Password policy**: Custom
  - Minimum length: 8
  - ✅ Contains uppercase letters
  - ✅ Contains lowercase letters  
  - ✅ Contains numbers
  - ⬜ Contains special characters
- **Multi-factor authentication**: No MFA

**Step 3: Configure sign-up experience**
- ✅ Enable self-service sign-up
- **Attribute verification**: ✅ Send email verification messages
- **Required attributes**: Email
- **Custom attributes**: None needed

**Step 4: Configure message delivery**
- **Email provider**: Send email with Cognito

**Step 5: Integrate your app**
- **User pool name**: `inventory-api-user-pool`
- **App client name**: `inventory-api-client`
- **Client secret**: ⬜ Don't generate a client secret
- **Authentication flows**: 
  - ✅ ALLOW_USER_PASSWORD_AUTH
  - ✅ ALLOW_REFRESH_TOKEN_AUTH

3. **Click "Create user pool"**

4. **📝 Save these values:**
   - **User Pool ID**: Found in "User pool overview" (format: us-east-1_xxxxxxxxx)
   - **App Client ID**: Found in "App integration" → "App clients" 

---

## 📝 Step 4: Update Environment Configuration

### 4.1 Update .env file
Replace the placeholder values in your `.env` file:

```bash
PORT=3000
API=/api
JWT_SECRET=ip/p7lfoPxRHRXvu5vQuOBLhIAgYp9xDIwD5wTF8Ek/sk3QxKUSR5pHp68Y/53ptu2cOevYkVhhOAfq9jJEHCQ==

# Replace these with your actual AWS values
AWS_ACCESS_KEY_ID=AKIA...your_access_key...
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
COGNITO_CLIENT_ID=your_client_id_here
```

---

## 🧪 Step 5: Test Everything

### 5.1 Test AWS Connection
```bash
python -c "
import boto3
try:
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print('✅ AWS Connection successful!')
    print(f'Account: {identity[\"Account\"]}')
    
    dynamodb = boto3.client('dynamodb')
    tables = dynamodb.list_tables()
    print(f'✅ DynamoDB tables: {tables[\"TableNames\"]}')
    
    cognito = boto3.client('cognito-idp')  
    pools = cognito.list_user_pools(MaxResults=10)
    print(f'✅ Cognito pools: {len(pools[\"UserPools\"])} found')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### 5.2 Restart FastAPI Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
✅ Table 'user_profiles' already exists.
✅ Table 'inventory_products' already exists.
INFO:     Application startup complete.
```

### 5.3 Test API Endpoints

**Go to**: http://localhost:8000/api/docs

**Test user signup:**
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
-H "Content-Type: application/json" \
-d '{
  "email": "test@youremail.com",
  "password": "TestPass123"
}'
```

**Expected response:**
```json
{
  "success": true,
  "message": "User created successfully. Please check email for verification."
}
```

---

## 🔒 Security Best Practices

### ✅ Do's:
- ✅ Use IAM users with minimal permissions
- ✅ Never commit AWS credentials to git
- ✅ Use different credentials for development/production
- ✅ Regularly rotate access keys
- ✅ Enable MFA on your AWS root account

### ❌ Don'ts:
- ❌ Don't use root account credentials
- ❌ Don't hardcode credentials in source code  
- ❌ Don't share credentials in chat/email
- ❌ Don't give broader permissions than needed

---

## 🚨 Troubleshooting

### Common Issues:

**1. "Invalid AWS credentials"**
```bash
# Check configuration
aws configure list
# Reconfigure if needed
aws configure
```

**2. "Table not found"**  
- Ensure tables exist in the same region as your credentials
- Check table names are exactly: `inventory_products`, `user_profiles`

**3. "Access denied"**
- Verify IAM policy is attached to your user
- Check the policy has all required permissions

**4. "User pool not found"**
- Verify COGNITO_USER_POOL_ID in .env matches AWS console
- Ensure User Pool is in the same region

**5. FastAPI startup errors**
- Check .env file has no extra spaces
- Verify all environment variables are set
- Restart the application after changing .env

---

## 💰 Cost Considerations

**This setup uses AWS free tier resources:**
- DynamoDB: 25GB storage + 25 units read/write capacity (free tier)
- Cognito: 50,000 monthly active users (free tier)
- IAM: Free service

**Estimated monthly cost: $0** (within free tier limits)

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all steps were followed correctly
3. Check AWS CloudTrail for detailed error logs
4. Ensure your AWS account has no billing issues

**Ready to proceed? Start with Step 1! 🚀**