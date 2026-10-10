from src.modules.base.exception import ServiceException, NotFoundData


class MaterialNotFound(NotFoundData):
    pass


class MaterialAlreadyExists(ServiceException):
    pass


class MaterialTranslationNotFound(NotFoundData):
    pass


class MaterialTranslationAlreadyExists(ServiceException):
    pass


class MaterialTranslationDeleteError(ServiceException):
    pass


class MaterialHasDependencies(ServiceException):
    pass


class MaterialGroupNotFound(NotFoundData):
    pass
