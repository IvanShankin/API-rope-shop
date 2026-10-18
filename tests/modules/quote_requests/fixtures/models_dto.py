from typing import Optional, List
from pydantic import BaseModel

from src.modules.configurator_setting.models import Currency
from src.modules.quote_requests.models import (
    ConfiguratorType,
    QuoteRequestStatus,
)


class CreateQuoteRopeItemFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    color_id: Optional[int] = None
    product_name_snapshot: Optional[str] = "Standard Yacht Rope"
    color_name_snapshot: Optional[str] = "Red"
    diameter_mm: float = 10.0
    length_m: float = 20.0
    quantity: int = 1
    price_per_meter_snapshot: float = 5.0
    total_rope_cost: float = 100.0
    end_a_type_id: Optional[int] = None
    end_a_name_snapshot: Optional[str] = None
    end_a_eye_size_cm: Optional[float] = None
    end_a_cost: float = 0.0
    end_b_type_id: Optional[int] = None
    end_b_name_snapshot: Optional[str] = None
    end_b_eye_size_cm: Optional[float] = None
    end_b_cost: float = 0.0


class CreateQuoteServiceItemFixtureDTO(BaseModel):
    splice_type_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    service_name_snapshot: Optional[str] = "Augspleiss"
    material_name_snapshot: Optional[str] = "Kern-Mantel"
    diameter_mm: float = 10.0
    eye_size_cm: Optional[float] = 15.0
    quantity: int = 1
    unit_price_snapshot: float = 15.0
    total_cost: float = 15.0


class CreateQuoteExtraItemFixtureDTO(BaseModel):
    extra_id: Optional[int] = None
    name_snapshot: Optional[str] = "Leather Protection"
    billing_type_snapshot: Optional[str] = "per_item"
    quantity: int = 1
    unit_price_snapshot: float = 15.0
    total_cost: float = 15.0


class CreateQuoteRequestFixtureDTO(BaseModel):
    request_number: Optional[str] = None
    configurator_type: ConfiguratorType = ConfiguratorType.ROPE_WITH_SPLICE
    name: str = "Test Customer"
    email: str = "customer@example.com"
    phone: Optional[str] = "+49 123 456789"
    comment: Optional[str] = "Standard test quote request"
    currency: Currency = Currency.EUR
    subtotal: float = 100.0
    urgent_surcharge: float = 0.0
    total_price: float = 100.0
    vat_rate: float = 0.0
    is_urgent: bool = False
    status: QuoteRequestStatus = QuoteRequestStatus.NEW
    rope_items: Optional[List[CreateQuoteRopeItemFixtureDTO]] = None
    service_items: Optional[List[CreateQuoteServiceItemFixtureDTO]] = None
    extra_items: Optional[List[CreateQuoteExtraItemFixtureDTO]] = None
