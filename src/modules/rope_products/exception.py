from src.modules.base.exception import ServiceException, NotFoundData


class RopeProductNotFound(NotFoundData):
    pass


class RopeProductAlreadyExists(ServiceException):
    pass


class RopeVariantNotFound(NotFoundData):
    pass


class RopeVariantAlreadyExists(ServiceException):
    pass


class RopeProductHasDependencies(ServiceException):
    pass


class MaterialGroupNotFound(NotFoundData):
    pass


class MaterialNotFound(NotFoundData):
    pass


class SpliceMaterialNotFound(NotFoundData):
    pass
