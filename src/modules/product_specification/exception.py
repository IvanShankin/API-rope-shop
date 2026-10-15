from src.modules.base.exception import ServiceException


class ProductSpecificationNotFound(ServiceException):
    pass


class ProductSpecificationAlreadyExists(ServiceException):
    pass


class ProductSpecificationInvalidBatch(ServiceException):
    pass


class ProductSpecificationTranslationNotFound(ServiceException):
    pass


class ProductSpecificationTranslationAlreadyExists(ServiceException):
    pass


class ProductSpecificationTranslationDeleteError(ServiceException):
    pass
