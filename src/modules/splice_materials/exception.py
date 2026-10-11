from src.modules.base.exception import ServiceException, NotFoundData

class SpliceMaterialNotFound(NotFoundData):
    pass

class SpliceMaterialAlreadyExists(ServiceException):
    pass

class SpliceMaterialHasDependencies(ServiceException):
    pass
