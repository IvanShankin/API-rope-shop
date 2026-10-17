from typing import Optional

from pydantic import BaseModel


class CreateWorkPhotoFixtureDTO(BaseModel):
    image_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
