from src.modules.base.exception import ServiceException, NotFoundData


class CategoryNotFound(NotFoundData):
    pass


class CategoryAlreadyExists(ServiceException):
    pass


class CategoryTranslationNotFound(NotFoundData):
    pass


class CategoryTranslationAlreadyExists(ServiceException):
    pass


class CategoryTranslationDeleteError(ServiceException):
    pass


class CategoryHasDependencies(ServiceException):
    pass
