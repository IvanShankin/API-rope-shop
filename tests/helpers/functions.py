import logging
import random
import string
from datetime import datetime
from typing import Type, Any, Dict

from dateutil.parser import parse
from orjson import orjson
from pydantic import BaseModel

from src.core.database.database import Base


def _get_dict(obj: Any) -> Dict:
    if isinstance(obj, dict): return obj
    elif isinstance(obj, bytes): return orjson.loads(obj)
    elif isinstance(obj, BaseModel): return obj.model_dump()
    elif isinstance(obj, Base): return obj.to_dict()
    else: raise RuntimeError(f"невалидный формат у: {obj}")


def comparison_models(Expected: Type | dict, Actual: Type | dict, keys_not_checked: list | None = None) -> bool:
    """Сравнивает две модели БД"""
    if keys_not_checked is None:
        keys_not_checked = []

    Expected = _get_dict(Expected)
    Actual = _get_dict(Actual)

    if not Actual:
        return False

    for key in Expected.keys():
        if key not in keys_not_checked:
            if key not in Actual:
                logging.getLogger("comparison_models").info(f"ключ '{key}' отсутствует в Actual")
                return False

            exp_val = Expected[key]
            act_val = Actual[key]

            if isinstance(exp_val, datetime) and not isinstance(act_val, datetime):
                try:
                    if exp_val != parse(str(act_val)):
                        logging.getLogger("comparison_models").info(f"ключ '{key}' не совпал: {exp_val} != {act_val}")
                        return False
                except Exception:
                    logging.getLogger("comparison_models").info(f"ключ '{key}' не удалось распарсить как дату")
                    return False
            elif isinstance(act_val, datetime) and not isinstance(exp_val, datetime):
                try:
                    if parse(str(exp_val)) != act_val:
                        logging.getLogger("comparison_models").info(f"ключ '{key}' не совпал: {exp_val} != {act_val}")
                        return False
                except Exception:
                    logging.getLogger("comparison_models").info(f"ключ '{key}' не удалось распарсить как дату")
                    return False
            elif isinstance(exp_val, dict) and isinstance(act_val, dict):
                if not comparison_models(exp_val, act_val, keys_not_checked):
                    return False
            else:
                from decimal import Decimal
                if hasattr(exp_val, "value") and not hasattr(act_val, "value"):
                    exp_val = exp_val.value
                if hasattr(act_val, "value") and not hasattr(exp_val, "value"):
                    act_val = act_val.value

                if (isinstance(exp_val, (int, float, Decimal)) and isinstance(act_val, (int, float, Decimal))
                        and not isinstance(exp_val, bool) and not isinstance(act_val, bool)):
                    if float(exp_val) != float(act_val):
                        logging.getLogger("comparison_models").info(f"ключ '{key}' не совпал: {exp_val} != {act_val}")
                        return False
                elif exp_val != act_val:
                    logging.getLogger("comparison_models").info(f"ключ '{key}' не совпал: {exp_val} != {act_val}")
                    return False

    return True


def random_string(length: int = 10) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))