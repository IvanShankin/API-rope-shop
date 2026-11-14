import pytest
from src.modules.base.database_model import Language, BaseModelWithRelationshipTranslation
from src.modules.products.models_dto import CONSTRUCTION_NAMES
from src.modules.notifications.service import NotificationService


def test_language_enum_french():
    assert Language.FRA == "fra"
    assert Language("fra") == Language.FRA
    assert Language("fr") == Language.FRA
    assert Language("fre") == Language.FRA
    assert Language("FR") == Language.FRA
    assert Language("FRA") == Language.FRA


def test_base_model_normalize_locale_french():
    assert BaseModelWithRelationshipTranslation._normalize_locale(Language.FRA) == "fr"
    assert BaseModelWithRelationshipTranslation._normalize_locale("fr") == "fr"
    assert BaseModelWithRelationshipTranslation._normalize_locale("fra") == "fr"
    assert BaseModelWithRelationshipTranslation._normalize_locale("fre") == "fr"
    assert BaseModelWithRelationshipTranslation._normalize_locale("FR") == "fr"


def test_notification_service_normalize_locale_french():
    assert NotificationService._normalize_locale("fr") == "fra"
    assert NotificationService._normalize_locale("fra") == "fra"
    assert NotificationService._normalize_locale("fre") == "fra"
    assert NotificationService._normalize_locale("FR") == "fra"


def test_construction_names_french():
    for key in ("hollow", "hm_core", "polyester_core", "none"):
        assert Language.FRA in CONSTRUCTION_NAMES[key]
        assert isinstance(CONSTRUCTION_NAMES[key][Language.FRA], str)
        assert len(CONSTRUCTION_NAMES[key][Language.FRA]) > 0
