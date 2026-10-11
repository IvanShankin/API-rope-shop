from src.modules.base.exception import ServiceException, NotFoundData


class ConfiguratorExtraNotFound(NotFoundData):
    pass


class ConfiguratorExtraAlreadyExists(ServiceException):
    pass


class ConfiguratorExtraTranslationNotFound(NotFoundData):
    pass


class ConfiguratorExtraTranslationAlreadyExists(ServiceException):
    pass


class ConfiguratorExtraTranslationDeleteError(ServiceException):
    pass


class ConfiguratorExtraHasDependencies(ServiceException):
    pass
