from typing import List, Optional
from pydantic import BaseModel

from src.modules.base.orm_dto import ORMDTO
from src.modules.splice_types.models_dto import SpliceTypeResponseDTO, SpliceTypeLocalizedResponseDTO


class RopeAllowedSpliceBase(BaseModel):
    product_id: int
    splice_type_id: int


class RopeAllowedSpliceCreate(BaseModel):
    product_id: int
    splice_type_id: int


class RopeAllowedSpliceBulkSetDTO(BaseModel):
    splice_type_ids: List[int]


class RopeAllowedSpliceResponseDTO(RopeAllowedSpliceBase, ORMDTO):
    splice_type: Optional[SpliceTypeResponseDTO] = None


class RopeAllowedSpliceLocalizedResponseDTO(RopeAllowedSpliceBase, ORMDTO):
    splice_type: Optional[SpliceTypeLocalizedResponseDTO] = None
