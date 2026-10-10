from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.rope_products.models import RopeProduct
    from src.modules.splice_types.models import SpliceType


class RopeAllowedSplice(Base):
    __tablename__ = "rope_allowed_splices"

    rope_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rope_products.product_id", ondelete="CASCADE"),
        primary_key=True
    )
    splice_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("splice_types.id", ondelete="CASCADE"),
        primary_key=True
    )

    __table_args__ = (
        UniqueConstraint("rope_product_id", "splice_type_id", name="uq_rope_allowed_splice"),
    )

    rope_product: Mapped["RopeProduct"] = relationship("RopeProduct", back_populates="allowed_splices")
    splice_type: Mapped["SpliceType"] = relationship("SpliceType")
