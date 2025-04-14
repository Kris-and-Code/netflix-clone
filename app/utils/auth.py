from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config import settings
from ..models.user import UserResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

security = HTTPBearer()
logger = logging.getLogger(__name__)

def create_access_token(user_id: str) -> str:
    """
    Create a new access token.
    
    Args:
        user_id: The user's ID
        
    Returns:
        JWT access token
    """
    expire = datetime.utcnow() + timedelta(minutes=15)  # Short-lived access token
    data = {
        "user_id": user_id,
        "token_type": "access",
        "exp": expire
    }
    return jwt.encode(data, settings.JWT_SECRET, algorithm="HS256")

def create_refresh_token(user_id: str) -> str:
    """
    Create a new refresh token.
    
    Args:
        user_id: The user's ID
        
    Returns:
        JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=30)  # Long-lived refresh token
    data = {
        "user_id": user_id,
        "token_type": "refresh",
        "exp": expire
    }
    return jwt.encode(data, settings.JWT_SECRET, algorithm="HS256")

def verify_refresh_token(token: str) -> str:
    """
    Verify a refresh token and return the user ID.
    
    Args:
        token: The refresh token to verify
        
    Returns:
        The user ID from the token
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload.get("user_id")
    except JWTError as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """
    Get the current authenticated user.
    
    Args:
        credentials: HTTP Authorization credentials containing access token
        
    Returns:
        UserResponse object for the authenticated user
        
    Raises:
        HTTPException: If the token is invalid or user not found
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    except JWTError as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    # Get user from database
    db = AsyncIOMotorClient(settings.MONGODB_URL).netflix
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    return UserResponse(**user) 