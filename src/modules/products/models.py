from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base
from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
)

if TYPE_CHECKING:
    from src.modules.categories.models import Category
    from src.modules.product_images.models import ProductImage
    from src.modules.rope_products.models import RopeConfiguratorSetting
    from src.modules.product_specification.models import ProductSpecification
    from src.modules.product_application.models import ProductAssignedApplication
    from src.modules.rope_product_color.models import ProductColor
    from src.modules.rope_allowed_splice.models import RopeAllowedSplice


class ProductType(str, Enum):
    ROPE = "rope"
    FINISHED_PRODUCT = "finished_product"
    HARDWARE = "hardware"


class PriceUnit(str, Enum):
    METER = "meter"
    PIECE = "piece"
    SET = "set"


class Product(BaseModelWithRelationshipTranslation):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    slug: Mapped[Optional[str]] = mapped_column(String(150), unique=True, nullable=True)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False, default=ProductType.ROPE.value)

    # Единица измерения тарификации ('meter', 'piece', 'set')
    price_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="meter", server_default="meter")

    # Интеграция с конфигуратором
    has_configurator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Параметры для фильтров каталога ('hollow', 'hm_core', 'polyester_core', 'none')
    construction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="products",
    )
    translations: Mapped[List["ProductTranslation"]] = relationship(
        "ProductTranslation",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductTranslation.id",
    )
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.index",
    )
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.index",
    )
    colors: Mapped[List["ProductColor"]] = relationship(
        "ProductColor",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductColor.index",
    )
    allowed_splices: Mapped[List["RopeAllowedSplice"]] = relationship(
        "RopeAllowedSplice",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    rope_configurator_settings: Mapped[Optional["RopeConfiguratorSetting"]] = relationship(
        "RopeConfiguratorSetting",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    specifications: Mapped[List["ProductSpecification"]] = relationship(
        "ProductSpecification",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSpecification.index",
    )
    assigned_applications: Mapped[List["ProductAssignedApplication"]] = relationship(
        "ProductAssignedApplication",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    @property
    def main_image_url(self) -> Optional[str]:
        if "images" not in self.__dict__ or not self.images:
            return None
        for img in self.images:
            if img.is_active and img.is_main:
                return img.image_url
        for img in self.images:
            if img.is_active:
                return img.image_url
        return None

    @property
    def price_from(self) -> Optional[float]:
        if "variants" not in self.__dict__ or not self.variants:
            return None
        active_prices = [
            float(v.price)
            for v in self.variants
            if getattr(v, "is_active", True) and getattr(v, "price", None) is not None
        ]
        return min(active_prices) if active_prices else None

    @property
    def size_min(self) -> Optional[float]:
        if "variants" not in self.__dict__ or not self.variants:
            return None
        active_sizes = [
            float(v.size_value)
            for v in self.variants
            if getattr(v, "is_active", True) and getattr(v, "size_value", None) is not None
        ]
        return min(active_sizes) if active_sizes else None

    @property
    def size_max(self) -> Optional[float]:
        if "variants" not in self.__dict__ or not self.variants:
            return None
        active_sizes = [
            float(v.size_value)
            for v in self.variants
            if getattr(v, "is_active", True) and getattr(v, "size_value", None) is not None
        ]
        return max(active_sizes) if active_sizes else None

    @property
    def variants_count(self) -> int:
        if "variants" not in self.__dict__ or not self.variants:
            return 0
        return sum(1 for v in self.variants if getattr(v, "is_active", True))

    @property
    def applications(self) -> list:
        if "assigned_applications" not in self.__dict__ or not self.assigned_applications:
            return []
        return [
            assigned.application
            for assigned in self.assigned_applications
            if getattr(assigned, "application", None) is not None
        ]


class ProductTranslation(BaseTranslation):
    __tablename__ = "product_translations"
    __table_args__ = (
        UniqueConstraint("product_id", "locale", name="uq_product_translations_product_locale"),
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="translations")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )

    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    size_value: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    breaking_load_dan: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    working_load_dan: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    working_stretch_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    weight_g: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="variants")
