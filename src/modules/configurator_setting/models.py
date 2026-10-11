import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, DateTime, func, Text, Numeric, Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import Base


class Currency(str, enum.Enum):
    EUR = "EUR"


class ConfiguratorSetting(Base):
    __tablename__ = "configurator_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    min_length_m: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    max_length_m: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)

    splice_allowance_until_mm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    splice_allowance_until_m: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    splice_allowance_over_m: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    urgent_surcharge_per_splice: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    urgent_max_splices: Mapped[int] = mapped_column(Integer, nullable=False)

    standard_turnaround_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    urgent_turnaround_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            values_callable=lambda x: [e.value for e in x],
            name="configurator_type",
            native_enum=False,
            length=50
        ),
        nullable=False,
        default=Currency.EUR.value,
    )

    vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    vat_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
