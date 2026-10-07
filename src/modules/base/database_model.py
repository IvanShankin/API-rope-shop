import enum
from datetime import datetime, UTC
from typing import TypeVar, Callable, Any
from pydantic import BaseModel

from sqlalchemy import Boolean, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import Base

# Объявляем generic тип, ограниченный классом Base
ModelType = TypeVar("ModelType", bound=Base)
DTOType = TypeVar("DTOType", bound="BaseModel")


class Language(str, enum.Enum):
    ENG = "eng"
    GER = "ger"


class BaseTranslation:
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    locale: Mapped[Language] = mapped_column(
        Enum(
            Language,
            values_callable=lambda x: [e.value for e in x],
            name="locale",
            native_enum=False,
            length=10
        ),
        nullable=False
    )


class BaseModelWithRelationshipTranslation(Base):
    """Наследовать только тому классу, что имеет связь с переводами (BaseTranslation)"""
    __abstract__ = True

    def _get_field_with_translation(
        self,
        field: Callable[[Any], Any],
        locale: Language,
        fallback: Language = Language.ENG
    ) -> Any | None:
        """Вернёт по указанному языку, если такого не найдёт, то вернёт по языку fallback, иначе первый попавшийся"""
        if not self.translations:
            return None

        for t in self.translations:
            if t.locale == locale:
                return field(t)

        if fallback:
            for t in self.translations:
                if t.locale == fallback:
                    return field(t)

        # вернём первый попавшийся, если ни запрошенный язык, ни fallback не найдены
        first_translation_value = field(self.translations[0])
        if first_translation_value:
            return first_translation_value
        return None


class SoftDeleteMixin:
    __abstract__ = True

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None