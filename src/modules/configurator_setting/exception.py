from src.modules.base.exception import ServiceException, NotFoundData


class ConfiguratorSettingNotFound(NotFoundData):
    pass


class ConfiguratorSettingValidationError(ServiceException):
    pass
