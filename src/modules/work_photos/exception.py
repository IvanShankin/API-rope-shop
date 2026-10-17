from src.modules.base.exception import DataAlreadyExists, HasDependencies, NotFoundData


class WorkPhotoNotFound(NotFoundData):
    pass


class WorkPhotoAlreadyExists(DataAlreadyExists):
    pass


class WorkPhotoHasDependencies(HasDependencies):
    pass
