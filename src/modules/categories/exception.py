from src.modules.base.exception import ServiceException, NotFoundData, DataAlreadyExists, DeleteError, HasDependencies


class CategoryNotFound(NotFoundData):
    pass


class CategoryAlreadyExists(DataAlreadyExists):
    pass


class CategoryTranslationNotFound(NotFoundData):
    pass


class CategoryTranslationAlreadyExists(DataAlreadyExists):
    pass


class CategoryTranslationDeleteError(DeleteError):
    pass


class CategoryHasDependencies(HasDependencies):
    pass
