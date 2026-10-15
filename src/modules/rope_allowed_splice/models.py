from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.products.models import Product
    from src.modules.splice_types.models import SpliceType


class RopeAllowedSplice(Base):
    __tablename__ = "rope_allowed_splices"

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    splice_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("splice_types.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        UniqueConstraint("product_id", "splice_type_id", name="uq_rope_allowed_splice"),
    )

    product: Mapped["Product"] = relationship("Product", back_populates="allowed_splices")
    splice_type: Mapped["SpliceType"] = relationship("SpliceType")
