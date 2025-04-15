from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config import settings
from ..models.user import UserResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging
from typing import Optional
import redis
from redis.exceptions import RedisError

security = HTTPBearer()
logger = logging.getLogger(__name__)

# Initialize Redis client for rate limiting
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )
except RedisError as e:
    logger.error(f"Redis connection error: {str(e)}")
    redis_client = None

def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

async def check_rate_limit(request: Request, key: str, limit: int, window: int) -> bool:
    """
    Check if request is within rate limit.
    
    Args:
        request: FastAPI request object
        key: Rate limit key
        limit: Maximum number of requests
        window: Time window in seconds
        
    Returns:
        bool: True if within limit, False otherwise
    """
    if not redis_client:
        return True  # Skip rate limiting if Redis is not available
        
    client_ip = get_client_ip(request)
    redis_key = f"rate_limit:{key}:{client_ip}"
    
    try:
        current = redis_client.get(redis_key)
        if current is None:
            redis_client.setex(redis_key, window, 1)
            return True
            
        current = int(current)
        if current >= limit:
            return False
            
        redis_client.incr(redis_key)
        return True
    except RedisError as e:
        logger.error(f"Rate limit check error: {str(e)}")
        return True  # Skip rate limiting on Redis error

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
        "exp": expire,
        "iat": datetime.utcnow()  # Issued at time
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
        "exp": expire,
        "iat": datetime.utcnow()  # Issued at time
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
            
        # Check if token was issued before user's last password change
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return user_id
    except JWTError as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """
    Get the current authenticated user.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials containing access token
        
    Returns:
        UserResponse object for the authenticated user
        
    Raises:
        HTTPException: If the token is invalid or user not found
    """
    try:
        # Check rate limit for authenticated requests
        if not await check_rate_limit(request, "auth", 100, 60):  # 100 requests per minute
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )
            
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