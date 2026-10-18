from src.modules.base.exception import ServiceException


class InvalidJWTToken(ServiceException):
    pass

class InvalidCredentials(ServiceException):
    pass


class UserInactive(ServiceException):
    pass