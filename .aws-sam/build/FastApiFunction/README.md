start project
python3 -m venv venv
source venv/bin/activate
uvicorn app.main:app --reload


post products sample
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
# InventoryBackend


==================================================================

Here’s a step-by-step guide to run your FastAPI app and test endpoints:

1. Prerequisites
Python 3.10+ installed
AWS account with DynamoDB and Cognito set up
Your .env file filled with real AWS and Cognito credentials
2. Install Dependencies
In your project directory, run:

If you don’t have a requirements.txt, install manually:

3. Set Up DynamoDB Tables
Go to AWS Console → DynamoDB → Create Table
Table name: inventory_products, Partition key: id (String)
Table name: user_profiles, Partition key: id (String)
No need for extra indexes for basic CRUD.
4. Set Up Cognito User Pool
Go to AWS Console → Cognito → Create User Pool
Note the User Pool ID and App Client ID (no secret)
Enable email as a required attribute and verification
5. Fill in .env
Replace placeholders with your real values:

6. Run the FastAPI App
From your project directory:

The API will be available at: http://localhost:8000/api/docs
7. Test Endpoints
Signup:
POST /api/auth/signup
Body:

Check your email for a confirmation code.
Confirm User (if you add a /confirm endpoint or via AWS Console):

Confirm the user using the code sent to email.
Login:
POST /api/auth/login
Body:

Copy the id_token from the response.
Authorize Requests:

In Swagger UI (/api/docs), click “Authorize” and paste:
Now you can call protected endpoints like /api/products and /api/profiles/me.
8. Example: Create Product
POST /api/products
Body:

You must be logged in and provide the JWT in the Authorization header.
Summary:

Install dependencies
Set up AWS resources
Fill .env
Run with uvicorn
Use /api/docs to test endpoints with Cognito JWT
Let me know if you want a script for table creation or a sample test with httpie or curl!- You must be logged in and provide the JWT in the Authorization header.

Summary:

Install dependencies
Set up AWS resources
Fill .env
Run with uvicorn
Use /api/docs to test endpoints with Cognito JWT
Let me know if you want a script for table creation or a sample test with httpie or curl!

