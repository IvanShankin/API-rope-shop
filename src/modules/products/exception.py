from src.modules.base.exception import ServiceException


class ProductNotFound(ServiceException):
    pass


class ProductAlreadyExists(ServiceException):
    pass


class ProductCategoryNotFound(ServiceException):
    pass


class ProductTranslationNotFound(ServiceException):
    pass


class ProductTranslationAlreadyExists(ServiceException):
    pass


class ProductTranslationDeleteError(ServiceException):
    pass


class ProductHasDependencies(ServiceException):
    pass
