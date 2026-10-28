from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from src.modules.base.orm_dto import ORMDTO, PaginatedResponse
from src.modules.base.database_model import Language
from src.modules.configurator_setting.models import Currency
from src.modules.quote_requests.models import (
    ConfiguratorType,
    QuoteRequestStatus,
)


class QuoteRequestSortBy(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TOTAL_PRICE = "total_price"
    REQUEST_NUMBER = "request_number"
    STATUS = "status"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


# ==================== Items Input DTOs ====================\n
class QuoteRopeItemCreate(BaseModel):
    product_id: int = Field(..., description="ID of the configured product")
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


class QuoteExtraItemCreate(BaseModel):
    extra_id: int = Field(..., description="ID of the configurator extra")


# ==================== QuoteRequest Input DTOs ====================

class QuoteRequestCreate(BaseModel):
    configurator_type: ConfiguratorType
    name: str = Field(..., min_length=1, max_length=255, description="Client full name")
    email: EmailStr = Field(..., description="Client email address")
    phone: Optional[str] = Field(None, max_length=100, description="Client phone number")
    comment: Optional[str] = Field(None, description="Client notes / wishes")
    is_urgent: bool = Field(default=False, description="Urgent order flag")
    locale: Optional[Language] = Field(Language.GER, description="Language to use for item snapshots")

    rope_items: List[QuoteRopeItemCreate] = Field(
        default_factory=list,
        description="List of configured ropes (for ROPE_WITH_SPLICE)"
    )
    service_items: List[QuoteServiceItemCreate] = Field(
        default_factory=list,
        description="List of services / splices (for LOOP_ONLY or SPLICE_ONLY)"
    )
    extra_items: List[QuoteExtraItemCreate] = Field(
        default_factory=list,
        description="List of configurator extras"
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
    subtotal: Optional[float] = Field(None, ge=0)
    urgent_surcharge: Optional[float] = Field(None, ge=0)
    total_price: Optional[float] = Field(None, ge=0)


# ==================== Internal / Resolved DTOs ====================

class ResolvedEndSpliceDTO(BaseModel):
    name_snapshot: Optional[str] = None
    cost: float = 0.0
    is_loop: bool = False


class ResolvedRopeItemDTO(BaseModel):
    product_id: int
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
    end_a_is_loop: bool = False
    end_b_type_id: Optional[int] = None
    end_b_name_snapshot: Optional[str] = None
    end_b_eye_size_cm: Optional[float] = None
    end_b_cost: float = 0.0
    end_b_is_loop: bool = False

    @property
    def total_cost(self) -> float:
        total = Decimal(str(self.total_rope_cost)) + Decimal(str(self.end_a_cost)) + Decimal(str(self.end_b_cost))
        return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

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
    is_loop: bool = False

    @property
    def splices_count(self) -> int:
        return self.quantity


class ResolvedExtraItemDTO(BaseModel):
    extra_id: int
    name_snapshot: str
    billing_type_snapshot: str
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteRequestTotalsDTO(BaseModel):
    subtotal: float
    urgent_surcharge: float
    total_price: float


class QuoteRopeItemInsertDTO(BaseModel):
    quote_request_id: int
    product_id: int
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


class QuoteExtraItemInsertDTO(BaseModel):
    quote_request_id: int
    extra_id: int
    name_snapshot: str
    billing_type_snapshot: str
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteRequestInsertDTO(BaseModel):
    request_number: str
    tracking_token: str
    locale: str = "ger"
    configurator_type: ConfiguratorType
    name: str
    email: str
    phone: Optional[str] = None
    comment: Optional[str] = None
    currency: Currency
    subtotal: float = 0.0
    urgent_surcharge: float = 0.0
    total_price: float
    vat_rate: float
    is_urgent: bool
    status: QuoteRequestStatus = QuoteRequestStatus.NEW


# ==================== Response DTOs ====================

class QuoteRopeItemResponseDTO(ORMDTO):
    id: int
    quote_request_id: int
    product_id: Optional[int] = None
    color_id: Optional[int] = None
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
    end_a_cost: float
    end_b_type_id: Optional[int] = None
    end_b_name_snapshot: Optional[str] = None
    end_b_eye_size_cm: Optional[float] = None
    end_b_cost: float
    total_cost: float


class QuoteServiceItemResponseDTO(ORMDTO):
    id: int
    quote_request_id: int
    splice_type_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    service_name_snapshot: str
    material_name_snapshot: str
    diameter_mm: float
    eye_size_cm: Optional[float] = None
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteExtraItemResponseDTO(ORMDTO):
    id: int
    quote_request_id: int
    extra_id: Optional[int] = None
    name_snapshot: str
    billing_type_snapshot: str
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteRequestResponseDTO(ORMDTO):
    id: int
    request_number: str
    configurator_type: ConfiguratorType
    name: str
    email: str
    phone: Optional[str] = None
    comment: Optional[str] = None
    currency: Currency
    subtotal: float
    urgent_surcharge: float
    total_price: float
    vat_rate: float
    is_urgent: bool
    status: QuoteRequestStatus
    created_at: datetime
    updated_at: datetime
    rope_items: List[QuoteRopeItemResponseDTO] = []
    service_items: List[QuoteServiceItemResponseDTO] = []
    extra_items: List[QuoteExtraItemResponseDTO] = []
    locale: str = "ger"
    tracking_token: Optional[str] = None
    tracking_url: Optional[str] = None


class QuoteRequestListResponseDTO(PaginatedResponse[QuoteRequestResponseDTO]):
    """Ответ со списком заявок и метаданными пагинации."""
    limit: int = 50


# ==================== Calculation (Dry-Run) DTOs ====================

class QuoteRequestCalculateDTO(BaseModel):
    configurator_type: ConfiguratorType
    is_urgent: bool = Field(default=False, description="Urgent order flag")
    locale: Optional[Language] = Field(Language.GER, description="Language to use for item snapshots")
    rope_items: List[QuoteRopeItemCreate] = Field(
        default_factory=list,
        description="List of configured ropes (for ROPE_WITH_SPLICE)"
    )
    service_items: List[QuoteServiceItemCreate] = Field(
        default_factory=list,
        description="List of services / splices (for LOOP_ONLY or SPLICE_ONLY)"
    )
    extra_items: List[QuoteExtraItemCreate] = Field(
        default_factory=list,
        description="List of configurator extras"
    )


class QuoteCalculationRopeItemDTO(BaseModel):
    product_id: int
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
    total_cost: float


class QuoteCalculationServiceItemDTO(BaseModel):
    splice_type_id: int
    splice_material_id: int
    service_name_snapshot: str
    material_name_snapshot: str
    diameter_mm: float
    eye_size_cm: Optional[float] = None
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteCalculationExtraItemDTO(BaseModel):
    extra_id: int
    name_snapshot: str
    billing_type_snapshot: str
    quantity: int
    unit_price_snapshot: float
    total_cost: float


class QuoteCalculationResponseDTO(BaseModel):
    configurator_type: ConfiguratorType
    currency: Currency
    subtotal: float
    urgent_surcharge: float
    total_price: float
    vat_rate: float
    is_urgent: bool
    rope_items: List[QuoteCalculationRopeItemDTO] = []
    service_items: List[QuoteCalculationServiceItemDTO] = []
    extra_items: List[QuoteCalculationExtraItemDTO] = []
