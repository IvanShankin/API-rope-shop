

class ServiceException(Exception):
    pass


class RepositoryException(Exception):
    pass


class NotFoundData(ServiceException):
    pass


class NoDataForUpdate(RepositoryException):
    pass

