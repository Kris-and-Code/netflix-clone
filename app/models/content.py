from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

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
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    duration: int = Field(..., gt=0)  # in seconds
    episode_number: int = Field(..., gt=0)
    season_number: int = Field(..., gt=0)
    thumbnail_url: HttpUrl
    video_url: HttpUrl
    release_date: datetime

class Season(BaseModel):
    season_number: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    episodes: List[Episode]
    release_date: datetime

class ContentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    type: ContentType
    genre: List[str] = Field(..., min_items=1)
    release_year: int = Field(..., gt=1900, le=datetime.now().year)
    duration: str
    thumbnail_url: HttpUrl
    video_url: HttpUrl
    rating: Optional[float] = Field(None, ge=0, le=10)
    content_rating: ContentRating = Field(default=ContentRating.PG13)

class ContentCreate(ContentBase):
    pass

class ContentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    type: Optional[ContentType] = None
    genre: Optional[List[str]] = Field(None, min_items=1)
    release_year: Optional[int] = Field(None, gt=1900, le=datetime.now().year)
    duration: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None
    video_url: Optional[HttpUrl] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    content_rating: Optional[ContentRating] = None

class ContentResponse(ContentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: PyObjectId

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class PaginatedContent(BaseModel):
    items: List[ContentResponse]
    total: int
    page: int
    size: int
    pages: int 