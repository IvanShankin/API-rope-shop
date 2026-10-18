from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ValidationError,
)


class ColorNotFound(NotFoundData):
    pass


class ColorAlreadyExists(DataAlreadyExists):
    pass


class ColorValidationError(ValidationError):
    pass


class ColorTranslationNotFound(NotFoundData):
    pass


class ColorTranslationAlreadyExists(DataAlreadyExists):
    pass


class ColorTranslationDeleteError(DeleteError):
    pass


class ColorHasDependencies(HasDependencies):
    pass
