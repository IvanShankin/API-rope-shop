from typing import Optional
from pydantic import BaseModel


class CreateRopeAllowedSpliceFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    splice_type_id: Optional[int] = None
