from src.modules.base.exception import NotFoundData, DataAlreadyExists, HasDependencies


class RopeProductNotFound(NotFoundData):
    pass


class RopeProductAlreadyExists(DataAlreadyExists):
    pass


class RopeVariantNotFound(NotFoundData):
    pass


class RopeVariantAlreadyExists(DataAlreadyExists):
    pass


class RopeProductHasDependencies(HasDependencies):
    pass


class MaterialGroupNotFound(NotFoundData):
    pass


class MaterialNotFound(NotFoundData):
    pass


class SpliceMaterialNotFound(NotFoundData):
    pass
