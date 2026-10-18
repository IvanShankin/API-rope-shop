from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ValidationError,
)


class MaterialNotFound(NotFoundData):
    pass


class MaterialAlreadyExists(DataAlreadyExists):
    pass


class MaterialValidationError(ValidationError):
    pass


class MaterialTranslationNotFound(NotFoundData):
    pass


class MaterialTranslationAlreadyExists(DataAlreadyExists):
    pass


class MaterialTranslationDeleteError(DeleteError):
    pass


class MaterialHasDependencies(HasDependencies):
    pass


class MaterialGroupNotFound(NotFoundData):
    pass
