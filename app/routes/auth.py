from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user import UserCreate, UserLogin, UserResponse
from ..utils.auth import create_access_token, create_refresh_token, verify_refresh_token
from ..schemas.responses import DataResponse
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings
import bcrypt
from bson import ObjectId
from datetime import datetime
import logging
from typing import Dict, Any

router = APIRouter()
security = HTTPBearer()
db = AsyncIOMotorClient(settings.MONGODB_URL).netflix

logger = logging.getLogger(__name__)

@router.post("/register", response_model=DataResponse[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register a new user.
    
    Args:
        user: UserCreate model containing email, password, and profile_name
        
    Returns:
        DataResponse containing access token and user information
    """
    try:
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
                    "profile_name": user.profile_name
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

@router.post("/login", response_model=DataResponse[Dict[str, Any]])
async def login(user_data: UserLogin):
    """
    Authenticate user and return tokens.
    
    Args:
        user_data: UserLogin model containing email and password
        
    Returns:
        DataResponse containing access token, refresh token and user information
    """
    try:
        user = await db.users.find_one({"email": user_data.email.lower()})
        if not user or not bcrypt.checkpw(
            user_data.password.encode(),
            user["password"].encode()
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        user_id = str(user["_id"])
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        # Update user with new refresh token and last login
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "refresh_token": refresh_token,
                    "last_login": datetime.utcnow()
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
                    "profile_name": user["profile_name"]
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

@router.post("/refresh-token", response_model=DataResponse[Dict[str, Any]])
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Generate new access token using refresh token.
    
    Args:
        credentials: HTTP Authorization credentials containing refresh token
        
    Returns:
        DataResponse containing new access token
    """
    try:
        refresh_token = credentials.credentials
        user_id = verify_refresh_token(refresh_token)
        
        user = await db.users.find_one({
            "_id": ObjectId(user_id),
            "refresh_token": refresh_token
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