from src.modules.base.exception import ServiceException


class ProductApplicationNotFound(ServiceException):
    pass


class ProductApplicationAlreadyExists(ServiceException):
    pass


class ProductApplicationHasDependencies(ServiceException):
    pass


class ProductApplicationTranslationNotFound(ServiceException):
    pass


class ProductApplicationTranslationAlreadyExists(ServiceException):
    pass


class ProductApplicationTranslationDeleteError(ServiceException):
    pass


class ProductAssignedApplicationAlreadyExists(ServiceException):
    pass


class ProductAssignedApplicationNotFound(ServiceException):
    pass
