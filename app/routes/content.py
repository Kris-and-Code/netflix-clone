from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from ..models.content import Content
from ..utils.auth import get_current_user
from ..utils.db import db

router = APIRouter()

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
    
    cursor = db.client.netflix.content.find(query).skip(skip).limit(limit)
    return await cursor.to_list(length=limit) 