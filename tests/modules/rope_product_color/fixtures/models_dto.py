from typing import Optional
from pydantic import BaseModel


class CreateRopeProductColorFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    color_id: Optional[int] = None
    index: Optional[int] = None
