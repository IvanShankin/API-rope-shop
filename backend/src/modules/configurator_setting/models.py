import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import Base


class Currency(str, enum.Enum):
    EUR = "EUR"


class ConfiguratorSetting(Base):
    __tablename__ = "configurator_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    min_length_m: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=1.0, server_default="1.0"
    )
    max_length_m: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=200.0, server_default="200.0"
    )

    splice_allowance_until_mm: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, default=12.0, server_default="12.0"
    )
    splice_allowance_until_m: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, default=0.6, server_default="0.6"
    )
    splice_allowance_over_m: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, default=1.0, server_default="1.0"
    )

    urgent_surcharge_per_splice: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=10.0, server_default="10.0"
    )
    urgent_max_splices: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default="10"
    )

    standard_turnaround_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=72, server_default="72"
    )
    urgent_turnaround_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=24, server_default="24"
    )

    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            values_callable=lambda x: [e.value for e in x],
            name="configurator_type",
            native_enum=False,
            length=50,
        ),
        nullable=False,
        default=Currency.EUR,
        server_default="EUR",
    )

    vat_rate: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0, server_default="0.0"
    )
    vat_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default="inkl. MwSt.", server_default="inkl. MwSt."
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __init__(
        self,
        min_length_m: float = 1.0,
        max_length_m: float = 200.0,
        splice_allowance_until_mm: float = 12.0,
        splice_allowance_until_m: float = 0.6,
        splice_allowance_over_m: float = 1.0,
        urgent_surcharge_per_splice: float = 10.0,
        urgent_max_splices: int = 10,
        standard_turnaround_hours: int = 72,
        urgent_turnaround_hours: int = 24,
        currency: Currency = Currency.EUR,
        vat_rate: float = 0.0,
        vat_note: Optional[str] = "inkl. MwSt.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            min_length_m=min_length_m,
            max_length_m=max_length_m,
            splice_allowance_until_mm=splice_allowance_until_mm,
            splice_allowance_until_m=splice_allowance_until_m,
            splice_allowance_over_m=splice_allowance_over_m,
            urgent_surcharge_per_splice=urgent_surcharge_per_splice,
            urgent_max_splices=urgent_max_splices,
            standard_turnaround_hours=standard_turnaround_hours,
            urgent_turnaround_hours=urgent_turnaround_hours,
            currency=currency,
            vat_rate=vat_rate,
            vat_note=vat_note,
            **kwargs,
        )
