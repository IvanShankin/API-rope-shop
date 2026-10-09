from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.rope_products.models import RopeProduct
    from src.modules.colors.models import Color


class RopeProductColor(Base):
    __tablename__ = "rope_product_colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rope_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rope_products.product_id", ondelete="CASCADE"),
        nullable=False
    )
    color_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("colors.id", ondelete="CASCADE"),
        nullable=False
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("rope_product_id", "color_id", name="uq_rope_product_color"),
    )

    rope_product: Mapped["RopeProduct"] = relationship("RopeProduct", back_populates="colors")
    color: Mapped["Color"] = relationship("Color")