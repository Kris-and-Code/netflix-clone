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
from ..utils.firebase import FirebaseDB
from ..config.settings import get_settings
import bcrypt
from datetime import datetime
import logging
from typing import Dict, Any, Optional
import re

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

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
        existing_user = await FirebaseDB.get_user_by_email(user.email)
        if existing_user:
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
        
        user_id = await FirebaseDB.create_user(user_dict)
        
        # Create tokens
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        # Update user with refresh token
        await FirebaseDB.update_user(user_id, {"refresh_token": refresh_token})
        
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
            detail="Internal server error"
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
    Authenticate user and return access token.
    
    Args:
        request: FastAPI request object
        user_data: UserLogin model containing email and password
        
    Returns:
        DataResponse containing access token, refresh token, and user information
    """
    try:
        # Check rate limit for login
        if not await check_rate_limit(request, "login", 10, 300):  # 10 login attempts per 5 minutes
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts"
            )
        
        # Get user from database
        user = await FirebaseDB.get_user_by_email(user_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Verify password
        if not bcrypt.checkpw(user_data.password.encode(), user["password"].encode()):
            # Update failed login attempts
            failed_attempts = user.get("failed_login_attempts", 0) + 1
            last_failed_login = datetime.utcnow()
            
            await FirebaseDB.update_user(user["id"], {
                "failed_login_attempts": failed_attempts,
                "last_failed_login": last_failed_login
            })
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                await FirebaseDB.update_user(user["id"], {"is_active": False})
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account locked due to multiple failed login attempts"
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Reset failed login attempts on successful login
        if user.get("failed_login_attempts", 0) > 0:
            await FirebaseDB.update_user(user["id"], {
                "failed_login_attempts": 0,
                "last_failed_login": None
            })
        
        # Update last login
        await FirebaseDB.update_user(user["id"], {"last_login": datetime.utcnow()})
        
        # Create new tokens
        access_token = create_access_token(user["id"])
        refresh_token = create_refresh_token(user["id"])
        
        # Update refresh token in database
        await FirebaseDB.update_user(user["id"], {"refresh_token": refresh_token})
        
        return DataResponse(
            success=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "profile_name": user["profile_name"],
                    "preferences": user.get("preferences", {}),
                    "my_list": user.get("my_list", [])
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
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
    Refresh access token using refresh token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials containing refresh token
        
    Returns:
        DataResponse containing new access token and refresh token
    """
    try:
        refresh_token = credentials.credentials
        user_id = verify_refresh_token(refresh_token)
        
        # Verify refresh token exists in database
        user = await FirebaseDB.get_user_by_id(user_id)
        if not user or user.get("refresh_token") != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        new_access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)
        
        # Update refresh token in database
        await FirebaseDB.update_user(user_id, {"refresh_token": new_refresh_token})
        
        return DataResponse(
            success=True,
            message="Token refreshed successfully",
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/logout",
    response_model=DataResponse[Dict[str, Any]],
    responses={
        200: {"model": DataResponse, "description": "Logout successful"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def logout(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Logout user by invalidating refresh token.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        DataResponse confirming logout
    """
    try:
        # Invalidate refresh token
        await FirebaseDB.update_user(current_user.id, {"refresh_token": None})
        
        return DataResponse(
            success=True,
            message="Logout successful",
            data={}
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 