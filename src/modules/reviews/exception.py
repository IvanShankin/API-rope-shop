from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ValidationError,
)


class ReviewNotFound(NotFoundData):
    pass


class ReviewAlreadyExists(DataAlreadyExists):
    pass


class ReviewValidationError(ValidationError):
    pass


class ReviewTranslationNotFound(NotFoundData):
    pass


class ReviewTranslationAlreadyExists(DataAlreadyExists):
    pass


class ReviewTranslationDeleteError(DeleteError):
    pass


class ReviewHasDependencies(HasDependencies):
    pass
