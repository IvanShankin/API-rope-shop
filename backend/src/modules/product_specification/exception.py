from src.modules.base.exception import ServiceException, DataAlreadyExists, DeleteError, NotFoundData


class ProductSpecificationNotFound(NotFoundData):
    pass


class ProductSpecificationAlreadyExists(DataAlreadyExists):
    pass


class ProductSpecificationInvalidBatch(ServiceException):
    pass


class ProductSpecificationTranslationNotFound(NotFoundData):
    pass


class ProductSpecificationTranslationAlreadyExists(DataAlreadyExists):
    pass


class ProductSpecificationTranslationDeleteError(DeleteError):
    pass
