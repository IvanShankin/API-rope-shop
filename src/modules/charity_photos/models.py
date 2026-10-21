from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base
from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
    Language,
)


class CharityPhoto(BaseModelWithRelationshipTranslation):
    __tablename__ = "charity_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    translations: Mapped[List["CharityPhotoTranslation"]] = relationship(
        "CharityPhotoTranslation",
        back_populates="charity_photo",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CharityPhotoTranslation.id",
    )

    @property
    def title(self) -> Optional[str]:
        state = inspect(self)
        if "translations" not in state.unloaded and self.translations:
            return self._get_field_with_translation(lambda t: t.title, Language.ENG, Language.ENG)
        return None

    @property
    def description(self) -> Optional[str]:
        state = inspect(self)
        if "translations" not in state.unloaded and self.translations:
            return self._get_field_with_translation(lambda t: t.description, Language.ENG, Language.ENG)
        return None


class CharityPhotoTranslation(BaseTranslation):
    __tablename__ = "charity_photo_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    charity_photo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("charity_photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    charity_photo: Mapped["CharityPhoto"] = relationship(
        "CharityPhoto",
        back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint("charity_photo_id", "locale", name="uq_charity_photo_id_locale"),
    )
