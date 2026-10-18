from src.modules.base.exception import NotFoundData, DataAlreadyExists


class RopeAllowedSpliceNotFound(NotFoundData):
    pass


class RopeAllowedSpliceAlreadyExists(DataAlreadyExists):
    pass


class RopeProductNotFound(NotFoundData):
    pass


class SpliceTypeNotFound(NotFoundData):
    pass
