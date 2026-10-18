from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ServiceException,
    ValidationError,
)


class ProductNotFound(NotFoundData):
    pass


class ProductAlreadyExists(DataAlreadyExists):
    pass


class ProductValidationError(ValidationError):
    pass


class ProductCategoryNotFound(NotFoundData):
    pass


class ProductTranslationNotFound(NotFoundData):
    pass


class ProductTranslationAlreadyExists(DataAlreadyExists):
    pass


class ProductTranslationDeleteError(DeleteError):
    pass


class ProductHasDependencies(HasDependencies):
    pass
