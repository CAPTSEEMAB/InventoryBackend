"""
Authentication routes using AWS Cognito
Simplified version with only signup and login
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from .utils import ok, bad
from .cognito_client import get_cognito_client

security = HTTPBearer()
router = APIRouter(prefix="/auth", tags=["Auth"])
COGNITO_CONFIGURED = (
    os.getenv('AWS_COGNITO_USER_POOL_ID') is not None and
    os.getenv('AWS_COGNITO_CLIENT_ID') is not None
)



class SignupBody(BaseModel):
    email: str
    password: str
    name: str

class LoginBody(BaseModel):
    email: str
    password: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from Cognito JWT token"""
    if not COGNITO_CONFIGURED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured"
        )
    
    try:
        cognito = get_cognito_client()
        result = cognito.verify_token(credentials.credentials)
        
        if not result['valid']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', 'Invalid token'),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return result['user']
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/signup")
def signup(body: SignupBody):
    """
    Create a new user account with AWS Cognito and auto-subscribe to notifications
    """
    if not COGNITO_CONFIGURED:
        return bad(503, "SERVICE_UNAVAILABLE", "Authentication service not configured")
    
    try:
        cognito = get_cognito_client()
        result = cognito.sign_up(
            email=body.email,
            password=body.password,
            name=body.name,
            role="USER"
        )
        
        if result['success']:
            # Auto-subscribe new user to product notifications
            try:
                # Simple direct subscription approach
                import boto3
                import os
                sns_client = boto3.client(
                    'sns',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.getenv('AWS_SNS_REGION', 'us-east-1')
                )
                
                # Create/get topic and subscribe
                topic_response = sns_client.create_topic(Name='product-notifications')
                topic_arn = topic_response['TopicArn']
                
                sns_client.subscribe(
                    TopicArn=topic_arn,
                    Protocol='email',
                    Endpoint=body.email
                )
                
            except Exception as sns_error:
                pass
            
            return ok(result['message'], {
                "token": result.get('token'),
                "user": result['user'],
                "requires_confirmation": result.get('requires_confirmation', False)
            })
        else:
            return bad(400, result.get('error', 'SIGNUP_FAILED'), result['message'])
            
    except Exception as e:
        return bad(500, "SIGNUP_EXCEPTION", "Unexpected error during signup", str(e))

@router.post("/login") 
def login(body: LoginBody):
    """
    Authenticate user with email and password using AWS Cognito
    """
    if not COGNITO_CONFIGURED:
        return bad(503, "SERVICE_UNAVAILABLE", "Authentication service not configured")
    
    try:
        cognito = get_cognito_client()
        result = cognito.login(body.email, body.password)
        
        if result['success']:
            return ok(result['message'], {
                "token": result['token'],
                "refresh_token": result.get('refresh_token'),
                "expires_in": result.get('expires_in'),
                "user": result['user']
            })
        else:
            return bad(401, result.get('error', 'LOGIN_FAILED'), result['message'])
                
    except Exception as e:
        return bad(500, "LOGIN_EXCEPTION", "Unexpected error during login", str(e))