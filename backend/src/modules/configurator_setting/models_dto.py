from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.configurator_setting.models import Currency


class ConfiguratorSettingResponseDTO(ORMDTO):
    id: int
    min_length_m: float
    max_length_m: float
    splice_allowance_until_mm: float
    splice_allowance_until_m: float
    splice_allowance_over_m: float
    urgent_surcharge_per_splice: float
    urgent_max_splices: int
    standard_turnaround_hours: int
    urgent_turnaround_hours: int
    currency: Currency
    vat_rate: float
    vat_note: Optional[str] = None
    updated_at: datetime


class ConfiguratorSettingUpdateDTO(BaseModel):
    min_length_m: Optional[float] = Field(None, gt=0, description="Minimum rope length in meters")
    max_length_m: Optional[float] = Field(None, gt=0, description="Maximum rope length in meters")
    splice_allowance_until_mm: Optional[float] = Field(None, gt=0, description="Threshold diameter in mm for splice allowance")
    splice_allowance_until_m: Optional[float] = Field(None, ge=0, description="Allowance length for ropes <= threshold")
    splice_allowance_over_m: Optional[float] = Field(None, ge=0, description="Allowance length for ropes > threshold")
    urgent_surcharge_per_splice: Optional[float] = Field(None, ge=0, description="Extra surcharge per splice for urgent orders")
    urgent_max_splices: Optional[int] = Field(None, ge=0, description="Maximum splices allowed for urgent order")
    standard_turnaround_hours: Optional[int] = Field(None, ge=0, description="Standard production turnaround hours")
    urgent_turnaround_hours: Optional[int] = Field(None, ge=0, description="Urgent production turnaround hours")
    currency: Optional[Currency] = None
    vat_rate: Optional[float] = Field(None, ge=0, description="VAT percentage")
    vat_note: Optional[str] = None
