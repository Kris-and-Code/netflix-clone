from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user import UserCreate, UserLogin, UserResponse, UserUpdate
from ..utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    check_rate_limit
)
from ..schemas.responses import DataResponse, ErrorResponse
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings
import bcrypt
from bson import ObjectId
from datetime import datetime
import logging
from typing import Dict, Any, Optional
import re

router = APIRouter()
security = HTTPBearer()
db = AsyncIOMotorClient(settings.MONGODB_URL).netflix
logger = logging.getLogger(__name__)

@router.post(
    "/register",
    response_model=DataResponse[Dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        429: {"model": ErrorResponse, "description": "Too Many Requests"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def register(request: Request, user: UserCreate):
    """
    Register a new user.
    
    Args:
        request: FastAPI request object
        user: UserCreate model containing email, password, and profile_name
        
    Returns:
        DataResponse containing access token, refresh token, and user information
    """
    try:
        # Check rate limit for registration
        if not await check_rate_limit(request, "register", 5, 3600):  # 5 registrations per hour
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts"
            )
        
        # Check if user exists
        if await db.users.find_one({"email": user.email.lower()}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user document
        user_dict = user.model_dump()
        user_dict["email"] = user_dict["email"].lower()
        user_dict["password"] = bcrypt.hashpw(
            user.password.encode(),
            bcrypt.gensalt()
        ).decode()
        user_dict["created_at"] = datetime.utcnow()
        user_dict["is_active"] = True
        user_dict["last_login"] = None
        user_dict["failed_login_attempts"] = 0
        user_dict["last_failed_login"] = None
        
        result = await db.users.insert_one(user_dict)
        user_id = str(result.inserted_id)
        
        # Create tokens
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        # Update user with refresh token
        await db.users.update_one(
            {"_id": result.inserted_id},
            {"$set": {"refresh_token": refresh_token}}
        )
        
        return DataResponse(
            success=True,
            message="Registration successful",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user_id,
                    "email": user.email,
                    "profile_name": user.profile_name,
                    "preferences": user.preferences
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not register user"
        )

@router.post(
    "/login",
    response_model=DataResponse[Dict[str, Any]],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Too Many Requests"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def login(request: Request, user_data: UserLogin):
    """
    Authenticate user and return tokens.
    
    Args:
        request: FastAPI request object
        user_data: UserLogin model containing email and password
        
    Returns:
        DataResponse containing access token, refresh token and user information
    """
    try:
        # Check rate limit for login attempts
        if not await check_rate_limit(request, "login", 10, 300):  # 10 attempts per 5 minutes
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts"
            )
        
        user = await db.users.find_one({"email": user_data.email.lower()})
        
        if not user:
            # Increment failed login attempts for non-existent user
            await db.users.update_one(
                {"email": user_data.email.lower()},
                {
                    "$inc": {"failed_login_attempts": 1},
                    "$set": {"last_failed_login": datetime.utcnow()}
                },
                upsert=True
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        if not bcrypt.checkpw(
            user_data.password.encode(),
            user["password"].encode()
        ):
            # Increment failed login attempts
            await db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$inc": {"failed_login_attempts": 1},
                    "$set": {"last_failed_login": datetime.utcnow()}
                }
            )
            
            # Check if account should be locked
            if user.get("failed_login_attempts", 0) >= 5:
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"is_active": False}}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account locked due to too many failed attempts"
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Reset failed login attempts on successful login
        user_id = str(user["_id"])
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "refresh_token": refresh_token,
                    "last_login": datetime.utcnow(),
                    "failed_login_attempts": 0,
                    "last_failed_login": None
                }
            }
        )
        
        return DataResponse(
            success=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user_id,
                    "email": user["email"],
                    "profile_name": user["profile_name"],
                    "preferences": user.get("preferences", {})
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not authenticate user"
        )

@router.post(
    "/refresh-token",
    response_model=DataResponse[Dict[str, Any]],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def refresh_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Generate new access token using refresh token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials containing refresh token
        
    Returns:
        DataResponse containing new access token
    """
    try:
        # Check rate limit for token refresh
        if not await check_rate_limit(request, "refresh", 20, 300):  # 20 refreshes per 5 minutes
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many token refresh attempts"
            )
        
        refresh_token = credentials.credentials
        user_id = verify_refresh_token(refresh_token)
        
        user = await db.users.find_one({
            "_id": ObjectId(user_id),
            "refresh_token": refresh_token,
            "is_active": True
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        new_access_token = create_access_token(user_id)
        
        return DataResponse(
            success=True,
            message="Token refreshed successfully",
            data={"access_token": new_access_token}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not refresh token"
        ) 