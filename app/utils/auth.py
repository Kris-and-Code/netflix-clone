from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config.settings import get_settings
from ..models.user import UserResponse
from ..utils.firebase import FirebaseAuth
import logging
from typing import Optional
import redis
from redis.exceptions import RedisError

security = HTTPBearer()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize Redis client for rate limiting
try:
    if settings.REDIS_URL:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    else:
        redis_client = None
        logger.info("No Redis URL provided, rate limiting disabled")
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
    return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")

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
        "iat": datetime.utcnow()
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")

def verify_access_token(token: str) -> str:
    """
    Verify and decode access token.
    
    Args:
        token: JWT access token
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("token_type")
        
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def verify_refresh_token(token: str) -> str:
    """
    Verify and decode refresh token.
    
    Args:
        token: JWT refresh token
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("token_type")
        
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """
    Get current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials
        
    Returns:
        UserResponse object for authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # First try to verify as JWT token
        user_id = verify_access_token(token)
        # TODO: Fetch user from Firebase using user_id
        # For now, return a mock user response
        return UserResponse(
            id=user_id,
            email="user@example.com",
            profile_name="User",
            preferences={},
            my_list=[],
            created_at=datetime.utcnow(),
            is_active=True
        )
    except HTTPException:
        # If JWT fails, try Firebase ID token
        try:
            decoded_token = await FirebaseAuth.verify_id_token(token)
            user_id = decoded_token.get("uid")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # TODO: Fetch user from Firebase using user_id
            # For now, return a mock user response
            return UserResponse(
                id=user_id,
                email=decoded_token.get("email", "user@example.com"),
                profile_name=decoded_token.get("name", "User"),
                preferences={},
                my_list=[],
                created_at=datetime.utcnow(),
                is_active=True
            )
        except Exception as e:
            logger.error(f"Firebase token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            ) 