import enum
from datetime import datetime
from typing import List, Optional, Callable, Any

from sqlalchemy import DateTime, String, Integer, func, Boolean, Enum, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base
from src.modules.base.database_model import BaseTranslation, Language, BaseModelWithRelationshipTranslation


class SpliceCategory(str, enum.Enum):
    LOOP = "loop"       # петля
    SPLICE = "splice"   # сращивание


class SpliceVisualType(str, enum.Enum):
    AUG_SPLICE = "aug_splice"
    TAKLING = "takling"
    PILOTAUGE = "pilotauge"
    ENDLESS_SPLICE = "endless_splice"
    SHACKLE = "shackle"
    KAUSCHE = "kausche"
    EXPOSED_EYE = "exposed_eye"
    SEWN_EYE = "sewn_eye"
    PROTECTION = "protection"
    LEATHER = "leather"
    FRICTION_RING = "friction_ring"
    SOFT_SHACKLE = "soft_shackle"
    GENERIC = "generic"


class SpliceType(BaseModelWithRelationshipTranslation):
    __tablename__ = "splice_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[SpliceCategory] = mapped_column(
        Enum(
            SpliceCategory,
            values_callable=lambda x: [e.value for e in x],
            name="category",
            native_enum=False,
            length=50
        ),
        nullable=False
    )
    visual_type: Mapped[SpliceVisualType] = mapped_column(
        Enum(
            SpliceVisualType,
            values_callable=lambda x: [e.value for e in x],
            name="visual_type",
            native_enum=False,
            length=50
        ),
        nullable=False
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[List["SpliceTypeTranslation"]] = relationship(
        "SpliceTypeTranslation", 
        back_populates="splice_type", 
        cascade="all, delete-orphan"
    )


class SpliceTypeTranslation(BaseTranslation):
    __tablename__ = "splice_type_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    splice_type_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("splice_types.id", ondelete="CASCADE"), 
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    splice_type: Mapped["SpliceType"] = relationship(
        "SpliceType", 
        back_populates="translations"
    )

    __table_args__ = (
        UniqueConstraint("splice_type_id", "locale", name="uq_splice_type_id_locale"),
    )
