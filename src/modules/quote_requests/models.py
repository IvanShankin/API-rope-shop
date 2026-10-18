from decimal import Decimal, ROUND_HALF_UP
import enum
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func, Text, Numeric, Enum, Sequence
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base
from src.modules.configurator_setting.models import Currency

quote_request_number_seq = Sequence("quote_request_number_seq", metadata=Base.metadata)

if TYPE_CHECKING:
    from src.modules.products.models import Product
    from src.modules.colors.models import Color
    from src.modules.splice_types.models import SpliceType
    from src.modules.splice_materials.models import SpliceMaterial
    from src.modules.configurator_extra.models import ConfiguratorExtra


class ConfiguratorType(str, enum.Enum):
    ROPE_WITH_SPLICE = "rope_with_splice"
    LOOP_ONLY = "loop_only"
    SPLICE_ONLY = "splice_only"


class QuoteRequestStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuoteRequest(Base):
    __tablename__ = "quote_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    configurator_type: Mapped[ConfiguratorType] = mapped_column(
        Enum(
            ConfiguratorType,
            values_callable=lambda x: [e.value for e in x],
            name="configurator_type",
            native_enum=False,
            length=50
        ),
        nullable=False
    )

    # Контакты заказчика
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Финансы и расчёт
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
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), server_default="0")
    urgent_surcharge: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), server_default="0")
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0")

    is_urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[QuoteRequestStatus] = mapped_column(
        Enum(
            QuoteRequestStatus,
            values_callable=lambda x: [e.value for e in x],
            name="quote_request_status",
            native_enum=False,
            length=30
        ),
        nullable=False,
        default=QuoteRequestStatus.NEW.value,
        server_default="new"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Позиции запроса
    rope_items: Mapped[List["QuoteRopeItem"]] = relationship(
        "QuoteRopeItem",
        back_populates="quote_request",
        cascade="all, delete-orphan",
    )
    service_items: Mapped[List["QuoteServiceItem"]] = relationship(
        "QuoteServiceItem",
        back_populates="quote_request",
        cascade="all, delete-orphan",
    )
    extra_items: Mapped[List["QuoteExtraItem"]] = relationship(
        "QuoteExtraItem",
        back_populates="quote_request",
        cascade="all, delete-orphan",
    )


class QuoteRopeItem(Base):
    """Позиция каната (для Конфигуратора 1: Канат с петлями или без)."""
    __tablename__ = "quote_rope_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_request_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quote_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Связь с товаром (nullable с защитой on delete set null)
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    color_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("colors.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Исторический снимок параметров каната
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    color_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    diameter_mm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    length_m: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    price_per_meter_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_rope_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Оснастка Конца A
    end_a_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("splice_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    end_a_name_snapshot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    end_a_eye_size_cm: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    end_a_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), server_default="0")

    # Оснастка Конца B
    end_b_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("splice_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    end_b_name_snapshot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    end_b_eye_size_cm: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    end_b_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"), server_default="0")

    # Relationships
    quote_request: Mapped["QuoteRequest"] = relationship("QuoteRequest", back_populates="rope_items")
    product: Mapped[Optional["Product"]] = relationship("Product")
    color: Mapped[Optional["Color"]] = relationship("Color")
    end_a_type: Mapped[Optional["SpliceType"]] = relationship("SpliceType", foreign_keys=[end_a_type_id])
    end_b_type: Mapped[Optional["SpliceType"]] = relationship("SpliceType", foreign_keys=[end_b_type_id])

    @property
    def total_cost(self) -> float:
        total = Decimal(str(self.total_rope_cost or 0)) + Decimal(str(self.end_a_cost or 0)) + Decimal(str(self.end_b_cost or 0))
        return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class QuoteServiceItem(Base):
    """Позиция услуги (для Конфигуратора 2: Только петли и Конфигуратора 3: Сращивание)."""
    __tablename__ = "quote_service_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_request_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quote_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Внешние ключи (nullable с защитой on delete set null)
    splice_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("splice_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    splice_material_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("splice_materials.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Исторический снимок услуги
    service_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    material_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    diameter_mm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    eye_size_cm: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    quote_request: Mapped["QuoteRequest"] = relationship("QuoteRequest", back_populates="service_items")
    splice_type: Mapped[Optional["SpliceType"]] = relationship("SpliceType")
    splice_material: Mapped[Optional["SpliceMaterial"]] = relationship("SpliceMaterial")


class QuoteExtraItem(Base):
    """Выбранная дополнительная опция к заявке (чехол, тест на разрыв, бирка и т.д.)."""
    __tablename__ = "quote_extra_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_request_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quote_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Внешний ключ на каталог доп. опций (SET NULL при удалении из админки)
    extra_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("configurator_extras.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Исторический снимок (Snapshot)
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_type_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)  # 'per_item', 'fixed', 'per_meter'

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    quote_request: Mapped["QuoteRequest"] = relationship("QuoteRequest", back_populates="extra_items")
    extra: Mapped[Optional["ConfiguratorExtra"]] = relationship("ConfiguratorExtra")
