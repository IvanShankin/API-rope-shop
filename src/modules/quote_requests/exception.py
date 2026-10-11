from src.modules.base.exception import ServiceException, NotFoundData


class QuoteRequestNotFound(NotFoundData):
    pass


class QuoteRopeItemNotFound(NotFoundData):
    pass


class QuoteServiceItemNotFound(NotFoundData):
    pass


class QuoteExtraItemNotFound(NotFoundData):
    pass


class ConfiguratorExtraNotFoundForQuote(NotFoundData):
    pass


class QuoteRequestValidationError(ServiceException):
    pass


class RopeProductNotFoundForQuote(NotFoundData):
    pass


class RopeVariantNotFoundForQuote(NotFoundData):
    pass


class ColorNotFoundForQuote(NotFoundData):
    pass


class ColorNotAllowedForProduct(ServiceException):
    pass


class SpliceTypeNotFoundForQuote(NotFoundData):
    pass


class SpliceMaterialNotFoundForQuote(NotFoundData):
    pass


class SplicePriceRuleNotFound(NotFoundData):
    pass


class RopeCannotBeSplicedError(ServiceException):
    pass


class SpliceNotAllowedForProductError(ServiceException):
    pass
