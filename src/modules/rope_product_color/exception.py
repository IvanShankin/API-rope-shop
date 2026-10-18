from src.modules.base.exception import NotFoundData, DataAlreadyExists


class RopeProductColorNotFound(NotFoundData):
    pass


class RopeProductColorAlreadyExists(DataAlreadyExists):
    pass


class RopeProductNotFound(NotFoundData):
    pass


class ColorNotFound(NotFoundData):
    pass
