from src.modules.base.exception import NotFoundData, DataAlreadyExists, HasDependencies


class SpliceMaterialNotFound(NotFoundData):
    pass

class SpliceMaterialAlreadyExists(DataAlreadyExists):
    pass

class SpliceMaterialHasDependencies(HasDependencies):
    pass
