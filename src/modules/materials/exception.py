from src.modules.base.exception import NotFoundData, DataAlreadyExists, DeleteError, HasDependencies


class MaterialNotFound(NotFoundData):
    pass


class MaterialAlreadyExists(DataAlreadyExists):
    pass


class MaterialTranslationNotFound(NotFoundData):
    pass


class MaterialTranslationAlreadyExists(DataAlreadyExists):
    pass


class MaterialTranslationDeleteError(DeleteError):
    pass


class MaterialHasDependencies(HasDependencies):
    pass


class MaterialGroupNotFound(NotFoundData):
    pass
