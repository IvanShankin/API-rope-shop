from typing import Optional, List, Any
from pydantic import BaseModel, model_validator
from sqlalchemy import inspect as sa_inspect

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
    rules: Optional[List[SplicePriceRuleWithRelationsResponseDTO]] = None

    @model_validator(mode="before")
    @classmethod
    def handle_unloaded_rules(cls, data: Any) -> Any:
        if hasattr(data, "_sa_instance_state"):
            state = sa_inspect(data)
            if "rules" in state.unloaded:
                return {
                    "id": getattr(data, "id", None),
                    "code": getattr(data, "code", None),
                    "name": getattr(data, "name", None),
                    "rules": None,
                }
        return data


class SpliceMaterialWithRulesResponseDTO(SpliceMaterialResponseDTO):
    rules: Optional[List[SplicePriceRuleWithRelationsResponseDTO]] = []


# ==================== Dependencies DTOs ====================

class SpliceMaterialPriceRuleDependencyDTO(BaseModel):
    id: int
    splice_type_id: int
    splice_type_code: Optional[str] = None
    diameter_from_mm: float
    diameter_to_mm: float
    price: float


class SpliceMaterialRopeDependencyDTO(BaseModel):
    product_id: int
    name: Optional[str] = None


class SpliceMaterialDependenciesDTO(BaseModel):
    has_dependencies: bool
    can_delete: bool
    rules_count: int
    ropes_count: int
    rules: List[SpliceMaterialPriceRuleDependencyDTO] = []
    ropes: List[SpliceMaterialRopeDependencyDTO] = []
