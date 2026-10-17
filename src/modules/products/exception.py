from src.modules.base.exception import ServiceException, DataAlreadyExists, DeleteError, HasDependencies, NotFoundData


class ProductNotFound(NotFoundData):
    pass


class ProductAlreadyExists(DataAlreadyExists):
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
