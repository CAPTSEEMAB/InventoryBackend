# Inventory Management API

## Quick Start
```bash
# Start project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Features
- ✅ **User Management** with AWS Cognito authentication
- ✅ **Product Management** with full CRUD operations
- ✅ **S3 File Storage** for catalogs and documents
- ✅ **SNS Notifications** for product events
- ✅ **SQS Message Processing** with retry logic and dead letter queue
- ✅ **DynamoDB** for data persistence

## API Endpoints
- **Auth**: `/api/auth/register`, `/api/auth/login`, `/api/auth/profile`
- **Products**: `/api/products/` (GET, POST, PUT, DELETE)
- **S3**: `/api/s3/upload`, `/api/s3/download`, `/api/s3/list`
- **SNS**: `/api/sns/subscribe`, `/api/sns/publish`
- **SQS**: `/api/sqs/stats`, `/api/sqs/health`, `/api/sqs/notification`

## Sample Product Data
```json
{
  "name": "Arabica Coffee Beans 1kg",
  "sku": "CFB-001",
  "category": "Coffee Beans",
  "supplier": "BeanCraft Roasters",
  "price": 18.99,
  "reorder_level": 10,
  "in_stock": 50,
  "description": "Premium roasted Arabica coffee beans",
  "movements": [
    { "movement_date": "2025-10-25", "type": "IN", "quantity": 50 },
    { "movement_date": "2025-10-26", "type": "OUT", "quantity": 5 }
  ]
}
```

## Infrastructure Setup
```bash
# Setup AWS infrastructure
python scripts/setup_aws_infrastructure.py
```
