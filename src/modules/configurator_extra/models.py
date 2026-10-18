from decimal import Decimal
import enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint, DateTime, func, Text, Numeric, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.modules.base.database_model import BaseTranslation, BaseModelWithRelationshipTranslation
from src.modules.configurator_setting.models import Currency


class BillingType(str, enum.Enum):
    FIXED = "fixed"         # Фиксированная цена за весь заказ
    PER_ITEM = "per_item"   # За каждое готовое изделие (за штуку)
    PER_METER = "per_meter" # За каждый метр длины каната


class ConfiguratorExtra(BaseModelWithRelationshipTranslation):
    """
    Формулы формирования надбавки к цене в зависимости от BillingType:
    FIXED = фиксированная надбавка
    PER_ITEM = price * quantity.
    PER_METER = price * length_m * quantity.
    """
    __tablename__ = "configurator_extras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            values_callable=lambda x: [e.value for e in x],
            name="currency",
            native_enum=False,
            length=50
        ),
        nullable=False,
        default=Currency.EUR.value,
    )
    billing_type: Mapped[BillingType] = mapped_column(
        Enum(
            BillingType,
            values_callable=lambda x: [e.value for e in x],
            name="billing_type",
            native_enum=False,
            length=50
        ),
        nullable=False,
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

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
    extra_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("configurator_extras.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    extra: Mapped["ConfiguratorExtra"] = relationship(
        "ConfiguratorExtra",
        back_populates="translations"
    )

    __table_args__ = (
        UniqueConstraint("extra_id", "locale", name="uq_extra_id_locale"),
    )
