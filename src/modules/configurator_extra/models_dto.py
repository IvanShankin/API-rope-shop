from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.database_model import Language
from src.modules.configurator_setting.models import Currency
from src.modules.configurator_extra.models import BillingType


# ==================== Translation DTOs ====================

class ConfiguratorExtraTranslationBase(BaseModel):
    locale: Language
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ConfiguratorExtraTranslationCreate(ConfiguratorExtraTranslationBase):
    pass


class ConfiguratorExtraTranslationInsert(ConfiguratorExtraTranslationCreate):
    extra_id: int


class ConfiguratorExtraTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ConfiguratorExtraTranslationResponseDTO(ConfiguratorExtraTranslationBase, ORMDTO):
    id: int
    extra_id: int


# ==================== Main Entity DTOs ====================

class ConfiguratorExtraBase(BaseModel):
    code: str
    price: float
    currency: Currency = Currency.EUR
    billing_type: BillingType
    index: int
    is_active: bool = True


class ConfiguratorExtraCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., ge=0)
    currency: Currency = Currency.EUR
    billing_type: BillingType
    index: Optional[int] = Field(
        None,
        ge=0,
        description="Optional index; if not provided, max_index + 1 will be used",
    )
    is_active: bool = True
    translations: List[ConfiguratorExtraTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required when creating a ConfiguratorExtra",
    )


class ConfiguratorExtraUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[Currency] = None
    billing_type: Optional[BillingType] = None
    is_active: Optional[bool] = None


class ConfiguratorExtraUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


# ==================== Response DTOs ====================

class ConfiguratorExtraResponseDTO(ORMDTO):
    id: int
    code: str
    price: float
    currency: Currency
    billing_type: BillingType
    index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    translations: List[ConfiguratorExtraTranslationResponseDTO] = []


class ConfiguratorExtraLocalizedResponseDTO(ORMDTO):
    id: int
    code: str
    price: float
    currency: Currency
    billing_type: BillingType
    index: int
    is_active: bool
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
