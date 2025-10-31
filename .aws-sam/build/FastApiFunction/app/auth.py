
import os
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
import boto3
from .utils import ok, bad, sign_jwt

# AWS Cognito config from .env
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

cognito = boto3.client(
    'cognito-idp',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupBody(BaseModel):
    email: EmailStr
    password: str
    name: str

@router.post("/signup")
def signup(body: SignupBody):
    try:
        resp = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=body.email,
            Password=body.password,
            UserAttributes=[
                {"Name": "email", "Value": body.email},
                {"Name": "name", "Value": body.name}
            ]
        )
        return ok("Signup successful. Please check your email to confirm your account.", {
            "user": {"email": body.email, "name": body.name},
            "email_sent": True,
            "next_step": "Confirm your email before logging in."
        })
    except cognito.exceptions.UsernameExistsException:
        return bad(400, "USER_EXISTS", "User already exists.")
    except Exception as e:
        return bad(500, "SIGNUP_EXCEPTION", str(e))

class LoginBody(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(body: LoginBody):
    try:
        resp = cognito.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": body.email,
                "PASSWORD": body.password
            }
        )
        id_token = resp["AuthenticationResult"]["IdToken"]
        access_token = resp["AuthenticationResult"]["AccessToken"]
        refresh_token = resp["AuthenticationResult"].get("RefreshToken")
        return ok("Login successful", {
            "id_token": id_token,
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    except cognito.exceptions.NotAuthorizedException:
        return bad(401, "INVALID_CREDENTIALS", "Incorrect username or password.")
    except cognito.exceptions.UserNotConfirmedException:
        return bad(401, "EMAIL_NOT_CONFIRMED", "Email not confirmed. Please check your inbox.")
    except Exception as e:
        return bad(500, "LOGIN_EXCEPTION", str(e))
