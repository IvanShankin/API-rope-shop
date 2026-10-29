from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ValidationError,
)


class SpliceTypeNotFound(NotFoundData):
    pass


class SpliceTypeAlreadyExists(DataAlreadyExists):
    pass


class SpliceTypeValidationError(ValidationError):
    pass


class SpliceTypeTranslationNotFound(NotFoundData):
    pass


class SpliceTypeTranslationAlreadyExists(DataAlreadyExists):
    pass


class SpliceTypeTranslationDeleteError(DeleteError):
    pass


class SpliceTypeHasDependencies(HasDependencies):
    pass
