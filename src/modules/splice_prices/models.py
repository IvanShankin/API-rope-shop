from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import  Integer, Boolean, ForeignKey, DateTime, func, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.splice_types.models import SpliceType
    from src.modules.splice_materials.models import SpliceMaterial


class SplicePriceRule(Base):
    __tablename__ = "splice_price_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    splice_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("splice_types.id", ondelete="CASCADE"), nullable=False)
    splice_material_id: Mapped[int] = mapped_column(Integer, ForeignKey("splice_materials.id", ondelete="CASCADE"), nullable=False)

    diameter_from_mm: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    diameter_to_mm: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    splice_type: Mapped["SpliceType"] = relationship("SpliceType")
    splice_material: Mapped["SpliceMaterial"] = relationship("SpliceMaterial", back_populates="rules")
