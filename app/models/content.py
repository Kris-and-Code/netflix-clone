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
    type: ContentType
    genres: List[str]
    release_date: datetime
    rating: ContentRating
    duration: Optional[int]  # for movies
    seasons: Optional[List[Season]]  # for series
    thumbnail_url: HttpUrl
    trailer_url: HttpUrl
    video_url: Optional[HttpUrl]
    cast: List[str]
    director: str
    languages: List[str]
    subtitles: List[str]
    tags: List[str]
    popularity_score: float = 0.0
    average_rating: float = 0.0
    total_ratings: int = 0
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow() 