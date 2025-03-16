from fastapi import APIRouter, HTTPException, status
from ..models.user import UserCreate, UserLogin, UserResponse
from ..utils.auth import create_access_token
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings
import bcrypt
from bson import ObjectId

router = APIRouter()
db = AsyncIOMotorClient(settings.MONGODB_URL).netflix

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
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
    
    try:
        result = await db.users.insert_one(user_dict)
        token = create_access_token(str(result.inserted_id))
        return {
            "token": token,
            "message": "Registration successful"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not register user"
        )

@router.post("/login", response_model=dict)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email.lower()})
    if not user or not bcrypt.checkpw(
        user_data.password.encode(),
        user["password"].encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = create_access_token(str(user["_id"]))
    return {
        "token": token,
        "message": "Login successful"
    } 