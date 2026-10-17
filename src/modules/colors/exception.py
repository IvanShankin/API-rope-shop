from src.modules.base.exception import NotFoundData, DataAlreadyExists, DeleteError, HasDependencies


class ColorNotFound(NotFoundData):
    pass


class ColorAlreadyExists(DataAlreadyExists):
    pass


class ColorTranslationNotFound(NotFoundData):
    pass


class ColorTranslationAlreadyExists(DataAlreadyExists):
    pass


class ColorTranslationDeleteError(DeleteError):
    pass


class ColorHasDependencies(HasDependencies):
    pass
