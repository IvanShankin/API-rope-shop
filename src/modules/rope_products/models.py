from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func, Text, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.material_groups.models import MaterialGroup
    from src.modules.rope_product_color.models import RopeProductColor
    from src.modules.rope_allowed_splice.models import RopeAllowedSplice
    from src.modules.splice_materials.models import SpliceMaterial


class RopeProduct(Base):
    __tablename__ = "rope_products"

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), primary_key=True)
    material_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("material_groups.id"), nullable=False)
    splice_material_id: Mapped[int] = mapped_column(Integer, ForeignKey("splice_materials.id"), nullable=False)

    construction: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    core_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    working_stretch_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    can_be_spliced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    material_group: Mapped["MaterialGroup"] = relationship("MaterialGroup")
    splice_material: Mapped["SpliceMaterial"] = relationship("SpliceMaterial")
    
    variants: Mapped[List["RopeVariant"]] = relationship("RopeVariant", back_populates="rope_product", cascade="all, delete-orphan")
    colors: Mapped[List["RopeProductColor"]] = relationship("RopeProductColor", back_populates="rope_product", cascade="all, delete-orphan")
    allowed_splices: Mapped[List["RopeAllowedSplice"]] = relationship("RopeAllowedSplice", back_populates="rope_product", cascade="all, delete-orphan")


class RopeVariant(Base):
    __tablename__ = "rope_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rope_product_id: Mapped[int] = mapped_column(Integer, ForeignKey("rope_products.product_id", ondelete="CASCADE"), nullable=False)

    diameter_mm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    breaking_load_dan: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    weight_g_per_m: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    price_per_meter: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    rope_product: Mapped["RopeProduct"] = relationship("RopeProduct", back_populates="variants")
