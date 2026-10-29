from src.modules.base.exception import (
    DataAlreadyExists,
    DeleteError,
    HasDependencies,
    NotFoundData,
    ValidationError,
)


class ConfiguratorExtraNotFound(NotFoundData):
    pass


class ConfiguratorExtraAlreadyExists(DataAlreadyExists):
    pass


class ConfiguratorExtraValidationError(ValidationError):
    pass


class ConfiguratorExtraTranslationNotFound(NotFoundData):
    pass


class ConfiguratorExtraTranslationAlreadyExists(DataAlreadyExists):
    pass


class ConfiguratorExtraTranslationDeleteError(DeleteError):
    pass


class ConfiguratorExtraHasDependencies(HasDependencies):
    pass
