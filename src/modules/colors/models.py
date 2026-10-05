from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base
from src.modules.base.database_model import BaseTranslation


class Color(Base):
    __tablename__ = "colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hex: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    translations: Mapped[List["ColorTranslation"]] = relationship(
        "ColorTranslation",
        back_populates="color",
        cascade="all, delete-orphan"
    )


class ColorTranslation(BaseTranslation):
    __tablename__ = "color_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    color_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("colors.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    color: Mapped["Color"] = relationship(
        "Color",
        back_populates="translations"
    )

    __table_args__ = (
        UniqueConstraint("color_id", "locale", name="uq_color_id_locale"),
    )

