from src.modules.base.exception import DataAlreadyExists, DeleteError, HasDependencies, NotFoundData


class ProductApplicationNotFound(NotFoundData):
    pass


class ProductApplicationAlreadyExists(DataAlreadyExists):
    pass


class ProductApplicationHasDependencies(HasDependencies):
    pass


class ProductApplicationTranslationNotFound(NotFoundData):
    pass


class ProductApplicationTranslationAlreadyExists(DataAlreadyExists):
    pass


class ProductApplicationTranslationDeleteError(DeleteError):
    pass


class ProductAssignedApplicationAlreadyExists(DataAlreadyExists):
    pass


class ProductAssignedApplicationNotFound(NotFoundData):
    pass
