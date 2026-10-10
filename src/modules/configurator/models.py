import enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint, DateTime, func, Text, Numeric, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base
from src.modules.base.database_model import BaseTranslation


class Currency(str, enum.Enum):
    EUR = "EUR"


class ConfiguratorExtra(Base):
    __tablename__ = "configurator_extras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
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
    billing_type: Mapped[str] = mapped_column(String(30), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[List["ConfiguratorExtraTranslation"]] = relationship(
        "ConfiguratorExtraTranslation",
        back_populates="extra",
        cascade="all, delete-orphan"
    )


class ConfiguratorExtraTranslation(BaseTranslation):
    __tablename__ = "configurator_extra_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extra_id: Mapped[int] = mapped_column(Integer, ForeignKey("configurator_extras.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    extra: Mapped["ConfiguratorExtra"] = relationship(
        "ConfiguratorExtra",
        back_populates="translations"
    )

    __table_args__ = (
        UniqueConstraint("extra_id", "locale", name="uq_extra_id_locale"),
    )


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



