import os
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import find_user_by_email

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
TOKEN_EXPIRY_MINUTES = int(os.getenv("TOKEN_EXPIRY_MINUTES", "60"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  

security = HTTPBearer()

def get_hashed_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(                         
    subject: str,
    is_premium: bool = False,                    
    expires_delta: timedelta = None
) -> str:
    """Create JWT access token with user info embedded"""
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    
    to_encode = {
        "exp": expires,
        "sub": str(subject),
        "is_premium": is_premium    
    }
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict | None:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user from token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = find_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def require_premium(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency for premium-only routes.
    Checks token directly (no extra DB query!)
    
    Usage: current_user = Depends(require_premium)
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    #  Check premium status FROM TOKEN (efficient!)
    if not payload.get("is_premium", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires a premium subscription. Upgrade to access!"
        )
    
    # Get full user from DB
    email = payload.get("sub")
    user = find_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user