from typing import Optional, List
from pydantic import BaseModel

from src.modules.configurator.models import Currency
from src.modules.quote_requests.models import (
    ConfiguratorType,
    QuoteRequestStatus,
)


class CreateQuoteRopeItemFixtureDTO(BaseModel):
    rope_product_id: Optional[int] = None
    color_id: Optional[int] = None
    product_name_snapshot: Optional[str] = None
    color_name_snapshot: Optional[str] = None
    diameter_mm: Optional[float] = None
    length_m: Optional[float] = None
    quantity: Optional[int] = None
    price_per_meter_snapshot: Optional[float] = None
    total_rope_cost: Optional[float] = None
    end_a_type_id: Optional[int] = None
    end_a_name_snapshot: Optional[str] = None
    end_a_eye_size_cm: Optional[float] = None
    end_a_cost: Optional[float] = None
    end_b_type_id: Optional[int] = None
    end_b_name_snapshot: Optional[str] = None
    end_b_eye_size_cm: Optional[float] = None
    end_b_cost: Optional[float] = None


class CreateQuoteServiceItemFixtureDTO(BaseModel):
    splice_type_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    service_name_snapshot: Optional[str] = None
    material_name_snapshot: Optional[str] = None
    diameter_mm: Optional[float] = None
    eye_size_cm: Optional[float] = None
    quantity: Optional[int] = None
    unit_price_snapshot: Optional[float] = None
    total_cost: Optional[float] = None


class CreateQuoteRequestFixtureDTO(BaseModel):
    request_number: Optional[str] = None
    configurator_type: Optional[ConfiguratorType] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    comment: Optional[str] = None
    currency: Optional[Currency] = None
    total_price: Optional[float] = None
    vat_rate: Optional[float] = None
    is_urgent: Optional[bool] = None
    status: Optional[QuoteRequestStatus] = None
    rope_items: List[CreateQuoteRopeItemFixtureDTO] = []
    service_items: List[CreateQuoteServiceItemFixtureDTO] = []
