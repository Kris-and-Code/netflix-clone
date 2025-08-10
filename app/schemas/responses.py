from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')

class ResponseBase(BaseModel):
    success: bool
    message: str
    timestamp: datetime = datetime.utcnow()

class DataResponse(ResponseBase, Generic[T]):
    data: Optional[T] = None

class ErrorResponse(ResponseBase):
    error_code: Optional[str] = None
    details: Optional[Any] = None

class PaginatedResponse(DataResponse[T]):
    page: int
    total_pages: int
    total_items: int
    items_per_page: int 