from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base
from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
)

if TYPE_CHECKING:
    from src.modules.categories.models import Category
    from src.modules.product_images.models import ProductImage
    from src.modules.rope_products.models import RopeConfiguratorSetting, ProductVariant
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
        for img in self.images:
            if img.is_active and img.is_main:
                return img.image_url
        for img in self.images:
            if img.is_active:
                return img.image_url
        return None


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


# ==================== Product Specifications (Catalog) ====================

class ProductSpecification(BaseModelWithRelationshipTranslation):
    __tablename__ = "product_specifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    product: Mapped["Product"] = relationship("Product", back_populates="specifications")
    translations: Mapped[List["ProductSpecificationTranslation"]] = relationship(
        "ProductSpecificationTranslation",
        back_populates="specification",
        cascade="all, delete-orphan",
    )


class ProductSpecificationTranslation(BaseTranslation):
    __tablename__ = "product_specification_translations"
    __table_args__ = (
        UniqueConstraint("specification_id", "locale", name="uq_product_spec_trans_spec_locale"),
    )

    specification_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_specifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)

    specification: Mapped["ProductSpecification"] = relationship(
        "ProductSpecification", back_populates="translations"
    )


# ==================== Product Applications (Catalog) ====================

class ProductApplication(BaseModelWithRelationshipTranslation):
    __tablename__ = "product_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    translations: Mapped[List["ProductApplicationTranslation"]] = relationship(
        "ProductApplicationTranslation",
        back_populates="application",
        cascade="all, delete-orphan",
    )
    assigned_products: Mapped[List["ProductAssignedApplication"]] = relationship(
        "ProductAssignedApplication",
        back_populates="application",
        cascade="all, delete-orphan",
    )


class ProductApplicationTranslation(BaseTranslation):
    __tablename__ = "product_application_translations"
    __table_args__ = (
        UniqueConstraint("application_id", "locale", name="uq_product_app_trans_app_locale"),
    )

    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    application: Mapped["ProductApplication"] = relationship(
        "ProductApplication", back_populates="translations"
    )


class ProductAssignedApplication(Base):
    __tablename__ = "product_assigned_applications"
    __table_args__ = (
        UniqueConstraint("product_id", "application_id", name="uq_product_assigned_app"),
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_applications.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product: Mapped["Product"] = relationship("Product", back_populates="assigned_applications")
    application: Mapped["ProductApplication"] = relationship("ProductApplication", back_populates="assigned_products")
