from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

# Pydantic Models
class UserBase(BaseModel):
    email: EmailStr
    profile_name: str = Field(..., min_length=2, max_length=50)
    preferences: Dict[str, Any] = Field(
        default_factory=lambda: {
            "language": "en",
            "maturity_level": "adult",
            "notifications_enabled": True
        }
    )

    @field_validator('profile_name')
    @classmethod
    def validate_profile_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Profile name can only contain letters, numbers, spaces, hyphens, and underscores')
        return v.strip()

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', v):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number, and one special character'
            )
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    profile_name: Optional[str] = Field(None, min_length=2, max_length=50)
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @field_validator('profile_name')
    @classmethod
    def validate_profile_name(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
                raise ValueError('Profile name can only contain letters, numbers, spaces, hyphens, and underscores')
            return v.strip()
        return v

class UserResponse(UserBase):
    id: str  # Changed from int to str for Firebase
    my_list: List[str] = Field(default_factory=list)
    created_at: str  # Changed from datetime to str for Firebase
    last_login: Optional[str] = None  # Changed from datetime to str for Firebase
    is_active: bool = True 