from src.modules.base.exception import (
    NotFoundData,
    ServiceException,
    ValidationError,
)


class ContactRequestNotFound(NotFoundData):
    """Исключение: запись контактных данных не найдена."""


class ContactRequestValidationError(ValidationError):
    """Исключение: ошибка валидации контактных данных."""
