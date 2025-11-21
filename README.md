# Inventory Management API# Inventory Management API



A production-ready RESTful API for inventory management built with FastAPI and AWS services.## Quick Start

```bash

## 🚀 Features# Start project

python3 -m venv .venv

- **🔐 User Authentication**: Secure signup/login with AWS Cognitosource .venv/bin/activate

- **📦 Product Management**: Complete CRUD operations for inventory items  pip install -r requirements.txt

- **📁 File Management**: S3 integration for bulk data operations and file storageuvicorn app.main:app --reload --host 127.0.0.1 --port 8000

- **📧 Real-time Notifications**: SNS integration for automatic product alerts```

- **⚡ Message Queuing**: SQS for reliable notification processing

- **🗄️ Data Storage**: DynamoDB for scalable product data management## Features

- ✅ **User Management** with AWS Cognito authentication

## ⚡ Quick Start- ✅ **Product Management** with full CRUD operations

- ✅ **S3 File Storage** for catalogs and documents

### Prerequisites- ✅ **SNS Notifications** for product events

- Python 3.9+- ✅ **SQS Message Processing** with retry logic and dead letter queue

- AWS Account with configured services- ✅ **DynamoDB** for data persistence

- AWS CLI configured with appropriate permissions

## API Endpoints

### Installation- **Auth**: `/api/auth/register`, `/api/auth/login`, `/api/auth/profile`

- **Products**: `/api/products/` (GET, POST, PUT, DELETE)

1. **Clone and setup**- **S3**: `/api/s3/upload`, `/api/s3/download`, `/api/s3/list`

```bash- **SNS**: `/api/sns/subscribe`, `/api/sns/publish`

git clone <repository-url>- **SQS**: `/api/sqs/stats`, `/api/sqs/health`, `/api/sqs/notification`

cd inventory_api

python -m venv .venv## Sample Product Data

source .venv/bin/activate  # On Windows: .venv\Scripts\activate```json

pip install -r requirements.txt{

```  "name": "Arabica Coffee Beans 1kg",

  "sku": "CFB-001",

2. **Configure environment**  "category": "Coffee Beans",

```bash  "supplier": "BeanCraft Roasters",

cp .env.example .env  "price": 18.99,

# Edit .env with your AWS credentials  "reorder_level": 10,

```  "in_stock": 50,

  "description": "Premium roasted Arabica coffee beans",

3. **Run the API**  "movements": [

```bash    { "movement_date": "2025-10-25", "type": "IN", "quantity": 50 },

uvicorn app.main:app --host 0.0.0.0 --port 8000    { "movement_date": "2025-10-26", "type": "OUT", "quantity": 5 }

```  ]

}

4. **Start background worker (optional)**```

```bash

python -m app.sqs.worker## Infrastructure Setup

``````bash

# Setup AWS infrastructure

**🌐 Access Points:**python scripts/setup_aws_infrastructure.py

- API: `http://localhost:8000````

- Documentation: `http://localhost:8000/docs`

## 📚 API Endpoints

### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/signup` | Create new user account |
| `POST` | `/api/auth/login` | User authentication |

### 📦 Products  
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products/` | List all products |
| `POST` | `/api/products/` | Create new product (triggers notifications) |
| `GET` | `/api/products/{id}` | Get product by ID |
| `PUT` | `/api/products/{id}` | Update product |
| `DELETE` | `/api/products/{id}` | Delete product |
| `GET` | `/api/products/by-category/{category}` | Get products by category |
| `GET` | `/api/products/by-sku/{sku}` | Get product by SKU |

### 📁 File Management (S3)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/s3/upload` | Upload file to S3 |
| `GET` | `/api/s3/files` | List uploaded files |
| `GET` | `/api/s3/download/{file_key}` | Download file |
| `GET` | `/api/s3/stats` | Storage statistics |

### 📧 Notifications (SQS/SNS)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sqs/notification` | Queue manual notification |
| `GET` | `/api/sqs/stats` | Queue statistics |
| `GET` | `/api/sqs/health` | Service health check |

## 🛠️ Configuration

### Environment Variables (.env)
```env
# Server Configuration  
PORT=8000
API_PREFIX=/api
ENVIRONMENT=production

# AWS Global Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# AWS Services
AWS_COGNITO_USER_POOL_ID=your_user_pool_id
AWS_COGNITO_CLIENT_ID=your_client_id  
AWS_S3_BUCKET_NAME=your-bucket-name

# Notifications
SNS_ENABLE_NOTIFICATIONS=true
SQS_ENABLE_NOTIFICATIONS=true
SQS_WORKER_BATCH_SIZE=5
SQS_WORKER_POLLING_INTERVAL=10
```

## 🏗️ AWS Infrastructure Setup

Use the provided scripts to set up AWS services:

```bash
# Setup all services at once
python scripts/setup_aws_infrastructure.py

# Or setup individually
python scripts/setup_dynamodb.py      # Product storage
python scripts/setup_cognito.py       # User authentication  
python scripts/setup_s3.py           # File storage
python scripts/setup_sns.py          # Email notifications
python scripts/setup_sqs.py          # Message queuing
```

## 📊 Sample Usage

### User Registration
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "phone_number": "+1234567890", 
    "name": "John Doe"
  }'
```

### Product Creation (Auto-triggers Notifications)
```bash
curl -X POST "http://localhost:8000/api/products/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Laptop",
    "sku": "LAPTOP-001",
    "category": "Electronics",
    "supplier": "TechCorp",
    "price": 999.99,
    "reorder_level": 10,
    "in_stock": 50,
    "description": "High-performance laptop"
  }'
```

### File Upload
```bash
curl -X POST "http://localhost:8000/api/s3/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@catalog.csv" \
  -F "bucket_name=your-bucket"
```

## 🔄 Production Deployment

### Single Server
```bash
# Production server with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Background worker for notifications (separate process)
python -m app.sqs.worker
```

### Process Management (PM2 Example)
```bash
# Install PM2
npm install -g pm2

# Start API server
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name inventory-api

# Start background worker  
pm2 start "python -m app.sqs.worker" --name inventory-worker

# Save configuration
pm2 save && pm2 startup
```

## 🏛️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │────│   AWS Cognito   │ (Authentication)
└─────────────────┘    └─────────────────┘
         │
         │              ┌─────────────────┐
         ├──────────────│   DynamoDB      │ (Product Data)
         │              └─────────────────┘
         │
         │              ┌─────────────────┐
         ├──────────────│      S3         │ (File Storage)  
         │              └─────────────────┘
         │
         │              ┌─────────────────┐
         └──────────────│   SNS + SQS     │ (Notifications)
                        └─────────────────┘
                               │
                        ┌─────────────────┐
                        │ Background      │ (Message Processing)
                        │ Worker          │
                        └─────────────────┘
```

## ✨ Key Features

- **🔄 Automatic Notifications**: Product creation/updates automatically notify all users
- **📧 Email Notifications**: SNS integration for reliable email delivery  
- **⚡ Background Processing**: SQS worker for non-blocking notifications
- **🔒 Secure Authentication**: JWT tokens with AWS Cognito
- **📈 Scalable Storage**: DynamoDB for high-performance data operations
- **📁 File Management**: S3 integration for bulk data and file uploads
- **🏥 Health Checks**: Built-in service monitoring and status endpoints

## 📖 Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc  
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

## 📄 License

MIT License - see LICENSE file for details.