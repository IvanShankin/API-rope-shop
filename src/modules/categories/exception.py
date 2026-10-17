from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ServiceException,
    ValidationError,
)


class CategoryNotFound(NotFoundData):
    pass


class CategoryAlreadyExists(DataAlreadyExists):
    pass


class CategoryValidationError(ValidationError):
    pass


class CategoryTranslationNotFound(NotFoundData):
    pass


class CategoryTranslationAlreadyExists(DataAlreadyExists):
    pass


class CategoryTranslationDeleteError(DeleteError):
    pass


class CategoryHasDependencies(HasDependencies):
    pass
