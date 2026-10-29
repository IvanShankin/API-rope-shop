from src.modules.base.exception import ServiceException, NotFoundData, ValidationError


class UserNotFound(NotFoundData):
    pass


class UserAlreadyExists(ServiceException):
    pass


# Backward compatibility alias
UserAlreadyExit = UserAlreadyExists


class IncorrectPassword(ValidationError):
    default_message = "Incorrect current password"
