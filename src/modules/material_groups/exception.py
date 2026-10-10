from src.modules.base.exception import ServiceException, NotFoundData


class MaterialGroupNotFound(NotFoundData):
    pass


class MaterialGroupAlreadyExists(ServiceException):
    pass


class MaterialGroupTranslationNotFound(NotFoundData):
    pass


class MaterialGroupTranslationAlreadyExists(ServiceException):
    pass


class MaterialGroupTranslationDeleteError(ServiceException):
    pass


class MaterialGroupHasDependencies(ServiceException):
    pass
