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
    DEFAULT_LOCALE,
    Language,
)


class WorkPhoto(BaseModelWithRelationshipTranslation):
    __tablename__ = "work_photos"

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

    translations: Mapped[List["WorkPhotoTranslation"]] = relationship(
        "WorkPhotoTranslation",
        back_populates="work_photo",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkPhotoTranslation.id",
    )

    @property
    def title(self) -> Optional[str]:
        state = inspect(self)
        if "translations" not in state.unloaded and self.translations:
            return self._get_field_with_translation(lambda t: t.title, DEFAULT_LOCALE, Language.ENG)
        return None

    @property
    def description(self) -> Optional[str]:
        state = inspect(self)
        if "translations" not in state.unloaded and self.translations:
            return self._get_field_with_translation(lambda t: t.description, DEFAULT_LOCALE, Language.ENG)
        return None


class WorkPhotoTranslation(BaseTranslation):
    __tablename__ = "work_photo_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_photo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("work_photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    work_photo: Mapped["WorkPhoto"] = relationship(
        "WorkPhoto",
        back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint("work_photo_id", "locale", name="uq_work_photo_id_locale"),
    )
