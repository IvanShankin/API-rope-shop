from typing import Optional

from pydantic import BaseModel


class CreateProductImageFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    image_url: Optional[str] = None
    is_main: Optional[bool] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
