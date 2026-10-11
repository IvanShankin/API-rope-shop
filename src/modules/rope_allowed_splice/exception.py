from src.modules.base.exception import ServiceException, NotFoundData


class RopeAllowedSpliceNotFound(NotFoundData):
    pass


class RopeAllowedSpliceAlreadyExists(ServiceException):
    pass


class RopeProductNotFound(NotFoundData):
    pass


class SpliceTypeNotFound(NotFoundData):
    pass
