from src.modules.base.exception import NotFoundData, DataAlreadyExists, DeleteError, HasDependencies


class SpliceTypeNotFound(NotFoundData):
    pass


class SpliceTypeAlreadyExists(DataAlreadyExists):
    pass


class SpliceTypeTranslationNotFound(NotFoundData):
    pass


class SpliceTypeTranslationAlreadyExists(DataAlreadyExists):
    pass


class SpliceTypeTranslationDeleteError(DeleteError):
    pass


class SpliceTypeHasDependencies(HasDependencies):
    pass
