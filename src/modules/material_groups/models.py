from typing import List
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base
from src.modules.base.database_model import BaseTranslation
from src.modules.materials.models import Material


class MaterialGroup(Base):
    __tablename__ = "material_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    translations: Mapped[List["MaterialGroupTranslation"]] = relationship(
        "MaterialGroupTranslation",
        back_populates="material_group",
        cascade="all, delete-orphan"
    )
    materials: Mapped[List["Material"]] = relationship(
        "Material",
        back_populates="group",
        cascade="all, delete-orphan"
    )


class MaterialGroupTranslation(BaseTranslation):
    __tablename__ = "material_group_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("material_groups.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    material_group: Mapped["MaterialGroup"] = relationship(
        "MaterialGroup",
        back_populates="translations"
    )

    __table_args__ = (
        UniqueConstraint("material_group_id", "locale", name="uq_material_group_id_locale"),
    )

