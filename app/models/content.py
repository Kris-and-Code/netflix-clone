from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from ..database import Base

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

# SQLAlchemy Models
class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # in seconds
    episode_number = Column(Integer, nullable=False)
    season_number = Column(Integer, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    video_url = Column(String, nullable=False)
    release_date = Column(DateTime(timezone=True), nullable=False)
    season_id = Column(Integer, ForeignKey("seasons.id"))
    season = relationship("Season", back_populates="episodes")

class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    season_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=False)
    release_date = Column(DateTime(timezone=True), nullable=False)
    content_id = Column(Integer, ForeignKey("contents.id"))
    content = relationship("Content", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season")

class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=False)
    type = Column(SQLEnum(ContentType), nullable=False)
    genre = Column(JSON, nullable=False)
    release_year = Column(Integer, nullable=False)
    duration = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    video_url = Column(String, nullable=False)
    rating = Column(Float, nullable=True)
    content_rating = Column(SQLEnum(ContentRating), default=ContentRating.PG13)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    seasons = relationship("Season", back_populates="content")

# Pydantic Models
class EpisodeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    duration: int = Field(..., gt=0)  # in seconds
    episode_number: int = Field(..., gt=0)
    season_number: int = Field(..., gt=0)
    thumbnail_url: HttpUrl
    video_url: HttpUrl
    release_date: datetime

class SeasonBase(BaseModel):
    season_number: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    episodes: List[EpisodeBase]
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
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int

    class Config:
        from_attributes = True

class PaginatedContent(BaseModel):
    items: List[ContentResponse]
    total: int
    page: int
    size: int
    pages: int 