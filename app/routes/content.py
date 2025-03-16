from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from ..models.content import Content
from ..models.user import UserResponse
from ..utils.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings
from bson import ObjectId

router = APIRouter()
db = AsyncIOMotorClient(settings.MONGODB_URL).netflix

@router.get("/", response_model=List[Content])
async def get_content(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    genre: Optional[str] = None,
    content_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    skip = (page - 1) * limit
    query = {}
    
    if genre:
        query["genre"] = genre
    if content_type:
        query["type"] = content_type
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    try:
        cursor = db.content.find(query).skip(skip).limit(limit)
        content = await cursor.to_list(length=limit)
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch content"
        )

@router.get("/{content_id}", response_model=Content)
async def get_content_by_id(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        content = await db.content.find_one({"_id": ObjectId(content_id)})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch content"
        ) 