from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint, DateTime, func, Text, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


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


class RopeProductColor(Base):
    __tablename__ = "rope_product_colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rope_product_id: Mapped[int] = mapped_column(Integer, ForeignKey("rope_products.product_id", ondelete="CASCADE"), nullable=False)
    color_id: Mapped[int] = mapped_column(Integer, ForeignKey("colors.id", ondelete="CASCADE"), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("rope_product_id", "color_id", name="uq_rope_product_color"),
    )


class RopeAllowedSplice(Base):
    __tablename__ = "rope_allowed_splices"

    rope_product_id: Mapped[int] = mapped_column(Integer, ForeignKey("rope_products.product_id", ondelete="CASCADE"), primary_key=True)
    splice_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("splice_types.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        UniqueConstraint("rope_product_id", "splice_type_id", name="uq_rope_allowed_splice"),
    )

