
class ServiceException(Exception):
    default_message = "Service exception"

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class RepositoryException(Exception):
    pass


class NotFoundData(ServiceException):
    default_message = "Not found data"


class DataAlreadyExists(ServiceException):
    default_message = "Data already exists"


class HasDependencies(ServiceException):
    default_message = "Has dependencies"


class DeleteError(ServiceException):
    default_message = "Delete error"


class ValidationError(ServiceException):
    default_message = "Validation error"


class NoDataForUpdate(ServiceException):
    default_message = "No data for update"


