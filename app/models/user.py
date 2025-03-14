from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime

class User(BaseModel):
    email: EmailStr
    password: str
    profile_name: str
    my_list: List[str] = []
    created_at: datetime = datetime.utcnow() 