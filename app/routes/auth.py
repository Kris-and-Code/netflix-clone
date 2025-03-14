from fastapi import APIRouter, HTTPException
from ..models.user import User
from ..utils.auth import create_token
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings
import bcrypt

router = APIRouter()
client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client.netflix

@router.post("/register")
async def register(user: User):
    # Check if user exists
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(400, "Email already registered")
    
    # Hash password
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    user.password = hashed.decode()
    
    # Save user
    result = await db.users.insert_one(user.dict())
    
    # Create token
    token = create_token(str(result.inserted_id))
    
    return {"token": token}

@router.post("/login")
async def login(email: str, password: str):
    user = await db.users.find_one({"email": email})
    if not user or not bcrypt.checkpw(
        password.encode(), 
        user["password"].encode()
    ):
        raise HTTPException(401, "Invalid credentials")
    
    token = create_token(str(user["_id"]))
    return {"token": token} 