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
    RU = "ru"
    EN = "en"
    DE = "de"
    RUS = "rus"
    ENG = "eng"
    GER = "ger"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            mapping = {
                "ru": cls.RU,
                "rus": cls.RUS,
                "en": cls.EN,
                "eng": cls.ENG,
                "de": cls.DE,
                "ger": cls.GER,
            }
            norm = value.lower()
            if norm in mapping:
                return mapping[norm]
        return super()._missing_(value)


class BaseTranslation(Base):
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

    @staticmethod
    def _normalize_locale(val: Any) -> str:
        if val is None:
            return ""
        s = val.value if hasattr(val, "value") else str(val)
        mapping = {
            "ru": "ru", "rus": "ru",
            "en": "en", "eng": "en",
            "de": "de", "ger": "de",
        }
        return mapping.get(s.lower(), s.lower())

    def _get_field_with_translation(
        self,
        field: Callable[[Any], Any],
        locale: Language,
        fallback: Language = Language.ENG
    ) -> Any | None:
        """Вернёт по указанному языку, если такого не найдёт, то вернёт по языку fallback, иначе первый попавшийся"""
        if not self.translations:
            return None

        target_norm = self._normalize_locale(locale)
        for t in self.translations:
            if self._normalize_locale(t.locale) == target_norm:
                return field(t)

        if fallback:
            fallback_norm = self._normalize_locale(fallback)
            for t in self.translations:
                if self._normalize_locale(t.locale) == fallback_norm:
                    return field(t)

        # вернём первый попавшийся, если ни запрошенный язык, ни fallback не найдены
        first_translation_value = field(self.translations[0])
        if first_translation_value:
            return first_translation_value
        return None
