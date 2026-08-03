from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    error: dict  # {"code": "...", "message": "..."}

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
