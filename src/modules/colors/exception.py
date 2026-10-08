from src.modules.base.exception import ServiceException, NotFoundData


class ColorNotFound(NotFoundData):
    pass


class ColorAlreadyExists(ServiceException):
    pass


class ColorTranslationNotFound(NotFoundData):
    pass


class ColorTranslationAlreadyExists(ServiceException):
    pass


class ColorTranslationDeleteError(ServiceException):
    pass


class ColorHasDependencies(ServiceException):
    pass
