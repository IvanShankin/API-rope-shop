from src.modules.base.exception import NotFoundData, DeleteError, DataAlreadyExists, HasDependencies


class ConfiguratorExtraNotFound(NotFoundData):
    pass


class ConfiguratorExtraAlreadyExists(DataAlreadyExists):
    pass


class ConfiguratorExtraTranslationNotFound(NotFoundData):
    pass


class ConfiguratorExtraTranslationAlreadyExists(DataAlreadyExists):
    pass


class ConfiguratorExtraTranslationDeleteError(DeleteError):
    pass


class ConfiguratorExtraHasDependencies(HasDependencies):
    pass
