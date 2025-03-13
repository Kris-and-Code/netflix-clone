from fastapi import APIRouter, HTTPException, Depends
from ..models.user import UserCreate, UserResponse
from ..utils.auth import get_password_hash, verify_password, create_access_token
from ..utils.db import db

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Check if user exists
    if await db.client.netflix.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["subscription"] = "basic"
    
    result = await db.client.netflix.users.insert_one(user_dict)
    
    return await db.client.netflix.users.find_one({"_id": result.inserted_id})

@router.post("/login")
async def login(email: str, password: str):
    user = await db.client.netflix.users.find_one({"email": email})
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token({"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"} 