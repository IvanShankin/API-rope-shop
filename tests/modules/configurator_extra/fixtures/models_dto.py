from typing import Optional
from pydantic import BaseModel

from src.modules.base.database_model import Language
from src.modules.configurator_setting.models import Currency
from src.modules.configurator_extra.models import BillingType


class CreateConfiguratorExtraFixtureDTO(BaseModel):
    code: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[Currency] = None
    billing_type: Optional[BillingType] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
    description: Optional[str] = None


class CreateConfiguratorExtraTranslationFixtureDTO(BaseModel):
    extra_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
    description: Optional[str] = None
