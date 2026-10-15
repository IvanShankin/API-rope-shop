from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
)

if TYPE_CHECKING:
    from src.modules.products.models import Product


class ProductSpecification(BaseModelWithRelationshipTranslation):
    """
    Это динамические характеристики товара.
    Сами характеристики хранятся в ProductSpecificationTranslation, работают по типу `ключ`: `значение`
    """
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