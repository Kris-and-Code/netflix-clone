from typing import List, Optional
from pydantic import BaseModel, HttpUrl
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

class Content(BaseModel):
    title: str
    description: str
    type: str  # "movie" or "series"
    genre: List[str]
    release_year: int
    duration: str
    thumbnail_url: str
    video_url: str
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow() 