from src.modules.base.exception import DataAlreadyExists, HasDependencies, NotFoundData


class ProductImageNotFound(NotFoundData):
    pass


class ProductImageAlreadyExists(DataAlreadyExists):
    pass


class ProductImageHasDependencies(HasDependencies):
    pass
