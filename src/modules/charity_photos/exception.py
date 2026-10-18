from src.modules.base.exception import DataAlreadyExists, HasDependencies, NotFoundData


class CharityPhotoNotFound(NotFoundData):
    pass


class CharityPhotoAlreadyExists(DataAlreadyExists):
    pass


class CharityPhotoHasDependencies(HasDependencies):
    pass


class CharityPhotoTranslationNotFound(NotFoundData):
    pass


class CharityPhotoTranslationAlreadyExists(DataAlreadyExists):
    pass


class CharityPhotoTranslationDeleteError(Exception):
    pass
