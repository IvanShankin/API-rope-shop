from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func, Text, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.products.models import Product
    from src.modules.material_groups.models import MaterialGroup
    from src.modules.materials.models import Material
    from src.modules.splice_materials.models import SpliceMaterial


class RopeConfiguratorSetting(Base):
    __tablename__ = "rope_configurator_settings"

    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    material_group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("material_groups.id", ondelete="RESTRICT"), nullable=False
    )
    material_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="SET NULL"), nullable=True
    )
    splice_material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("splice_materials.id", ondelete="RESTRICT"), nullable=False
    )

    construction: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    core_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    can_be_spliced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="rope_configurator_settings")
    material_group: Mapped["MaterialGroup"] = relationship("MaterialGroup")
    material: Mapped[Optional["Material"]] = relationship("Material")
    splice_material: Mapped["SpliceMaterial"] = relationship("SpliceMaterial")


# Re-export ProductVariant from products.models for backward compatibility
from src.modules.products.models import ProductVariant
