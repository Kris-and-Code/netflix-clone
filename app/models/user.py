from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SubscriptionType(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    profile_name: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    profile_name: str
    subscription: SubscriptionType
    created_at: datetime

class UserInDB(UserResponse):
    hashed_password: str 