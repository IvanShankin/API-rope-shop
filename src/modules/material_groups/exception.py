from src.modules.base.exception import NotFoundData, DataAlreadyExists, DeleteError, HasDependencies


class MaterialGroupNotFound(NotFoundData):
    pass


class MaterialGroupAlreadyExists(DataAlreadyExists):
    pass


class MaterialGroupTranslationNotFound(NotFoundData):
    pass


class MaterialGroupTranslationAlreadyExists(DataAlreadyExists):
    pass


class MaterialGroupTranslationDeleteError(DeleteError):
    pass


class MaterialGroupHasDependencies(HasDependencies):
    pass
