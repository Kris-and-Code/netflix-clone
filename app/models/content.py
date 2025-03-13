from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"

class Content(BaseModel):
    title: str
    description: str
    type: ContentType
    genre: List[str]
    release_year: int
    rating: Optional[float]
    duration: str
    thumbnail_url: Optional[str]
    video_url: Optional[str]
    trailer_url: Optional[str]
    cast: List[str]
    director: str 