from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.modules.base.database_model import BaseTranslation, BaseModelWithRelationshipTranslation

if TYPE_CHECKING:
    from src.modules.material_groups.models import MaterialGroup


class Material(BaseModelWithRelationshipTranslation):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("material_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    group: Mapped["MaterialGroup"] = relationship(
        "MaterialGroup",
        back_populates="materials"
    )
    translations: Mapped[List["MaterialTranslation"]] = relationship(
        "MaterialTranslation",
        back_populates="material",
        cascade="all, delete-orphan"
    )


class MaterialTranslation(BaseTranslation):
    __tablename__ = "material_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    material: Mapped["Material"] = relationship(
        "Material",
        back_populates="translations"
    )

    __table_args__ = (
        UniqueConstraint("material_id", "locale", name="uq_material_id_locale"),
    )
