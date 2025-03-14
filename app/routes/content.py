from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from ..models.content import Content
from ..utils.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings

router = APIRouter()
client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client.netflix

@router.get("/", response_model=List[Content])
async def get_content(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    genre: Optional[str] = None,
    content_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
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
    
    cursor = db.content.find(query).skip(skip).limit(limit)
    content = await cursor.to_list(length=limit)
    return content

@router.get("/{content_id}")
async def get_content_by_id(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    content = await db.content.find_one({"_id": content_id})
    if not content:
        raise HTTPException(404, "Content not found")
    return content 