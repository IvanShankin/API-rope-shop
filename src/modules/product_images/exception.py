from src.modules.base.exception import ServiceException


class ProductImageNotFound(ServiceException):
    pass


class ProductImageAlreadyExists(ServiceException):
    pass


class ProductImageHasDependencies(ServiceException):
    pass
