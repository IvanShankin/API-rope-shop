from typing import Optional
from pydantic import BaseModel


class CreateRopeProductFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    material_group_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    construction: Optional[str] = None
    can_be_spliced: Optional[bool] = None
