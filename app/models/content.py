from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"
    DOCUMENTARY = "documentary"

class ContentRating(str, Enum):
    G = "G"
    PG = "PG"
    PG13 = "PG-13"
    R = "R"
    NC17 = "NC-17"

class Episode(BaseModel):
    title: str
    description: str
    duration: int  # in seconds
    episode_number: int
    season_number: int
    thumbnail_url: HttpUrl
    video_url: HttpUrl
    release_date: datetime

class Season(BaseModel):
    season_number: int
    title: str
    description: str
    episodes: List[Episode]
    release_date: datetime

class ContentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    type: ContentType
    genre: List[str] = Field(..., min_items=1)
    release_year: int = Field(..., le=datetime.now().year)
    duration: str
    thumbnail_url: HttpUrl
    video_url: HttpUrl
    rating: Optional[float] = Field(None, ge=0, le=10)

class ContentCreate(ContentBase):
    pass

class ContentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    type: Optional[ContentType] = None
    genre: Optional[List[str]] = Field(None, min_items=1)
    release_year: Optional[int] = Field(None, le=datetime.now().year)
    duration: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None
    video_url: Optional[HttpUrl] = None
    rating: Optional[float] = Field(None, ge=0, le=10)

class ContentResponse(ContentBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True
        populate_by_name = True

class PaginatedContent(BaseModel):
    items: List[ContentResponse]
    total: int
    page: int
    size: int
    pages: int 