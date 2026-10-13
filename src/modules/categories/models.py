from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base
from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
)

if TYPE_CHECKING:
    from src.modules.products.models import Product


class Category(BaseModelWithRelationshipTranslation):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    translations: Mapped[List["CategoryTranslation"]] = relationship(
        "CategoryTranslation",
        back_populates="category",
        cascade="all, delete-orphan",
    )
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
    )


class CategoryTranslation(BaseTranslation):
    __tablename__ = "category_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint("category_id", "locale", name="uq_category_id_locale"),
    )
