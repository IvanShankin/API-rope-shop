from src.modules.base.exception import DataAlreadyExists, HasDependencies, NotFoundData


class CharityPhotoNotFound(NotFoundData):
    pass


class CharityPhotoAlreadyExists(DataAlreadyExists):
    pass


class CharityPhotoHasDependencies(HasDependencies):
    pass
