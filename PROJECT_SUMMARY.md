# Inventory API

FastAPI inventory management system with AWS DynamoDB and Cognito authentication.

## Stack
- FastAPI 0.111+
- AWS DynamoDB
- AWS Cognito  
- JWT Authentication
- Python 3.10+

## API Endpoints

### Authentication (`/api/auth/`)
- `POST /signup` - User registration
- `POST /login` - User authentication

### Products (`/api/products/`)
- `GET /` - Get all products
- `POST /` - Create product
- `GET /{id}` - Get product by ID
- `PUT /{id}` - Update product
- `DELETE /{id}` - Delete product

## Environment Variables
```env
PORT=3000
API=/api
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_COGNITO_USER_POOL_ID=your_pool_id
AWS_COGNITO_CLIENT_ID=your_client_id
```

## Setup
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --port 8000 --host 0.0.0.0
```

Access: http://localhost:8000/api/docs