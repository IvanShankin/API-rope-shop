from src.modules.base.exception import ServiceException, NotFoundData


class UserNotFound(NotFoundData):
    pass


class UserAlreadyExists(ServiceException):
    pass


# Backward compatibility alias
UserAlreadyExit = UserAlreadyExists

