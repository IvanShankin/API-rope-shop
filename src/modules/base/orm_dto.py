from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Единый стандарт пагинированного ответа для списочных эндпоинтов."""
    items: List[T]
    total: int
    skip: int = 0
    limit: Optional[int] = None
