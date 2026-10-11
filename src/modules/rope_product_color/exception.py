from src.modules.base.exception import ServiceException, NotFoundData


class RopeProductColorNotFound(NotFoundData):
    pass


class RopeProductColorAlreadyExists(ServiceException):
    pass


class RopeProductNotFound(NotFoundData):
    pass


class ColorNotFound(NotFoundData):
    pass
