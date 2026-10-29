from src.modules.base.exception import NotFoundData, ValidationError


class SplicePriceRuleNotFound(NotFoundData):
    pass


class SplicePriceRuleValidationError(ValidationError):
    pass
