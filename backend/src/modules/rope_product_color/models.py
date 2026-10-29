from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.products.models import Product
    from src.modules.colors.models import Color


class ProductColor(Base):
    __tablename__ = "product_colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    color_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("colors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "color_id", name="uq_product_color"),
    )

    product: Mapped["Product"] = relationship("Product", back_populates="colors")
    color: Mapped["Color"] = relationship("Color")
