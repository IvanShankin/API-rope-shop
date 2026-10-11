from typing import Optional, List
from pydantic import BaseModel

from src.modules.base.orm_dto import ORMDTO
from src.modules.splice_prices.models_dto import SplicePriceRuleWithRelationsResponseDTO


class SpliceMaterialBase(BaseModel):
    code: str
    name: str


class SpliceMaterialCreate(SpliceMaterialBase):
    pass


class SpliceMaterialUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None


class SpliceMaterialResponseDTO(SpliceMaterialBase, ORMDTO):
    id: int


class SpliceMaterialWithRulesResponseDTO(SpliceMaterialResponseDTO):
    rules: List[SplicePriceRuleWithRelationsResponseDTO] = []
