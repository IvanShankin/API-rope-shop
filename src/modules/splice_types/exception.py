from src.modules.base.exception import ServiceException, NotFoundData


class SpliceTypeNotFound(NotFoundData):
    pass


class SpliceTypeAlreadyExists(ServiceException):
    pass


class SpliceTypeTranslationNotFound(NotFoundData):
    pass


class SpliceTypeTranslationAlreadyExists(ServiceException):
    pass


class SpliceTypeTranslationDeleteError(ServiceException):
    pass
