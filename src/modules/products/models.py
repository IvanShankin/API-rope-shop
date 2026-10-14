from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
)

if TYPE_CHECKING:
    from src.modules.categories.models import Category
    from src.modules.product_images.models import ProductImage
    from src.modules.rope_products.models import RopeProduct


class ProductType(str, Enum):
    ROPE = "rope"
    FINISHED_PRODUCT = "finished_product"
    HARDWARE = "hardware"


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
    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
    rope_product: Mapped[Optional["RopeProduct"]] = relationship(
        "RopeProduct",
        uselist=False,
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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="translations")
