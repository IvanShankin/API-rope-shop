from src.modules.base.exception import (
    DataAlreadyExists,
    NotFoundData,
    ServiceException,
    ValidationError,
)


class ContentBlockNotFound(NotFoundData):
    """Исключение, если блок контента не найден."""


class ContentBlockAlreadyExists(DataAlreadyExists):
    """Исключение при попытке создания блока с уже существующим block_code."""


class ContentBlockValidationError(ValidationError):
    """Ошибка валидации данных блока контента."""
