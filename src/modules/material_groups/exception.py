from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ValidationError,
)


class MaterialGroupNotFound(NotFoundData):
    pass


class MaterialGroupAlreadyExists(DataAlreadyExists):
    pass


class MaterialGroupValidationError(ValidationError):
    pass


class MaterialGroupTranslationNotFound(NotFoundData):
    pass


class MaterialGroupTranslationAlreadyExists(DataAlreadyExists):
    pass


class MaterialGroupTranslationDeleteError(DeleteError):
    pass


class MaterialGroupHasDependencies(HasDependencies):
    pass
