from typing import Optional
from pydantic import BaseModel

from src.modules.configurator_setting.models import Currency


class CreateConfiguratorSettingFixtureDTO(BaseModel):
    min_length_m: Optional[float] = None
    max_length_m: Optional[float] = None
    splice_allowance_until_mm: Optional[float] = None
    splice_allowance_until_m: Optional[float] = None
    splice_allowance_over_m: Optional[float] = None
    urgent_surcharge_per_splice: Optional[float] = None
    urgent_max_splices: Optional[int] = None
    standard_turnaround_hours: Optional[int] = None
    urgent_turnaround_hours: Optional[int] = None
    currency: Optional[Currency] = None
    vat_rate: Optional[float] = None
    vat_note: Optional[str] = None
