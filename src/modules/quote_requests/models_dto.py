from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.database_model import Language
from src.modules.configurator.models import Currency
from src.modules.quote_requests.models import (
    ConfiguratorType,
    QuoteRequestStatus,
)


# ==================== Items Input DTOs ====================

class QuoteRopeItemCreate(BaseModel):
    rope_product_id: int = Field(..., description="ID of the configured rope product")
    color_id: int = Field(..., description="ID of the selected color")
    diameter_mm: float = Field(..., gt=0, description="Diameter in mm")
    length_m: float = Field(..., gt=0, description="Rope length in meters")
    quantity: int = Field(default=1, ge=1, description="Quantity of pieces")
    end_a_type_id: Optional[int] = Field(None, description="Splice/termination type ID for End A")
    end_a_eye_size_cm: Optional[float] = Field(None, ge=0, description="Eye size in cm for End A")
    end_b_type_id: Optional[int] = Field(None, description="Splice/termination type ID for End B")
    end_b_eye_size_cm: Optional[float] = Field(None, ge=0, description="Eye size in cm for End B")


class QuoteServiceItemCreate(BaseModel):
    splice_type_id: int = Field(..., description="ID of the splice / service type")
    splice_material_id: int = Field(..., description="Tariff / material group ID for splice")
    diameter_mm: float = Field(..., gt=0, description="Rope diameter in mm")
    eye_size_cm: Optional[float] = Field(None, ge=0, description="Eye size in cm")
    quantity: int = Field(default=1, ge=1, description="Quantity")


# ==================== QuoteRequest Input DTOs ====================

class QuoteRequestCreate(BaseModel):
    configurator_type: ConfiguratorType
    name: str = Field(..., min_length=1, max_length=255, description="Client full name")
    email: EmailStr = Field(..., description="Client email address")
    phone: Optional[str] = Field(None, max_length=100, description="Client phone number")
    comment: Optional[str] = Field(None, description="Client notes / wishes")
    is_urgent: bool = Field(default=False, description="Urgent order flag")
    locale: Optional[Language] = Field(Language.ENG, description="Language to use for item snapshots")

    rope_items: List[QuoteRopeItemCreate] = Field(
        default_factory=list,
        description="List of configured ropes (for ROPE_WITH_SPLICE)"
    )
    service_items: List[QuoteServiceItemCreate] = Field(
        default_factory=list,
        description="List of services / splices (for LOOP_ONLY or SPLICE_ONLY)"
    )


class QuoteRequestUpdateStatusDTO(BaseModel):
    status: QuoteRequestStatus


class QuoteRequestUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=100)
    comment: Optional[str] = None
    status: Optional[QuoteRequestStatus] = None
    is_urgent: Optional[bool] = None
    total_price: Optional[float] = Field(None, ge=0)


# ==================== Internal / Resolved DTOs ====================

class ResolvedEndSpliceDTO(BaseModel):
    name_snapshot: Optional[str] = None
    cost: float = 0.0


class ResolvedRopeItemDTO(BaseModel):
    rope_product_id: int
    color_id: int
    product_name_snapshot: str
    color_name_snapshot: str
    diameter_mm: float
    length_m: float
    quantity: int
    price_per_meter_snapshot: float
    total_rope_cost: float
    end_a_type_id: Optional[int] = None
    end_a_name_snapshot: Optional[str] = None
    end_a_eye_size_cm: Optional[float] = None
    end_a_cost: float = 0.0
    end_b_type_id: Optional[int] = None
    end_b_name_snapshot: Optional[str] = None
    end_b_eye_size_cm: Optional[float] = None
    end_b_cost: float = 0.0

    @property
    def total_cost(self) -> float:
        return round(self.total_rope_cost + self.end_a_cost + self.end_b_cost, 2)

    @property
    def splices_count(self) -> int:
        count = 0
        if self.end_a_type_id is not None:
            count += 1
        if self.end_b_type_id is not None:
            count += 1
        return count * self.quantity


class ResolvedServiceItemDTO(BaseModel):
    splice_type_id: int
    splice_material_id: int
    service_name_snapshot: str
    material_name_snapshot: str
    diameter_mm: float
    eye_size_cm: Optional[float] = None
    quantity: int
    unit_price_snapshot: float
    total_cost: float

    @property
    def splices_count(self) -> int:
        return self.quantity


class QuoteRequestTotalsDTO(BaseModel):
    subtotal: float
    urgent_surcharge: float
    total_price: float


class QuoteRopeItemInsertDTO(BaseModel):
    quote_request_id: int
    rope_product_id: int
    color_id: int
    product_name_snapshot: str
    color_name_snapshot: str
    diameter_mm: float
    length_m: float
    quantity: int
    price_per_meter_snapshot: float
    total_rope_cost: float
    end_a_type_id: Optional[int] = None
    end_a_name_snapshot: Optional[str] = None
    end_a_eye_size_cm: Optional[float] = None
    end_a_cost: float = 0.0
    end_b_type_id: Optional[int] = None
    end_b_name_snapshot: Optional[str] = None
    end_b_eye_size_cm: Optional[float] = None
    end_b_cost: float = 0.0


class QuoteServiceItemInsertDTO(BaseModel):
    quote_request_id: int
    splice_type_id: int
    splice_material_id: int
    service_name_snapshot: str
    material_name_snapshot: str
    diameter_mm: float
    eye_size_cm: Optional[float] = None
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteRequestInsertDTO(BaseModel):
    request_number: str
    configurator_type: ConfiguratorType
    name: str
    email: str
    phone: Optional[str] = None
    comment: Optional[str] = None
    currency: Currency
    total_price: float
    vat_rate: float
    is_urgent: bool
    status: QuoteRequestStatus = QuoteRequestStatus.NEW


# ==================== Response DTOs ====================

class QuoteRopeItemResponseDTO(ORMDTO):
    id: int
    quote_request_id: int
    rope_product_id: Optional[int]
    color_id: Optional[int]
    product_name_snapshot: str
    color_name_snapshot: str
    diameter_mm: float
    length_m: float
    quantity: int
    price_per_meter_snapshot: float
    total_rope_cost: float
    end_a_type_id: Optional[int]
    end_a_name_snapshot: Optional[str]
    end_a_eye_size_cm: Optional[float]
    end_a_cost: float
    end_b_type_id: Optional[int]
    end_b_name_snapshot: Optional[str]
    end_b_eye_size_cm: Optional[float]
    end_b_cost: float


class QuoteServiceItemResponseDTO(ORMDTO):
    id: int
    quote_request_id: int
    splice_type_id: Optional[int]
    splice_material_id: Optional[int]
    service_name_snapshot: str
    material_name_snapshot: str
    diameter_mm: float
    eye_size_cm: Optional[float]
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteRequestResponseDTO(ORMDTO):
    id: int
    request_number: str
    configurator_type: ConfiguratorType
    name: str
    email: str
    phone: Optional[str]
    comment: Optional[str]
    currency: Currency
    total_price: float
    vat_rate: float
    is_urgent: bool
    status: QuoteRequestStatus
    created_at: datetime
    updated_at: datetime
    rope_items: List[QuoteRopeItemResponseDTO] = []
    service_items: List[QuoteServiceItemResponseDTO] = []


class QuoteRequestShortResponseDTO(ORMDTO):
    id: int
    request_number: str
    configurator_type: ConfiguratorType
    name: str
    email: str
    phone: Optional[str]
    currency: Currency
    total_price: float
    vat_rate: float
    is_urgent: bool
    status: QuoteRequestStatus
    created_at: datetime
    updated_at: datetime
    items_count: int = 0
