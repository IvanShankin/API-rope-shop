from src.modules.colors.models import Color, ColorTranslation
from src.modules.colors.repository import ColorRepository, ColorTranslationRepository
from src.modules.colors.service import ColorService
from src.modules.colors.depends import get_color_service
from src.modules.colors.views import router as colors_router

__all__ = [
    "Color",
    "ColorTranslation",
    "ColorRepository",
    "ColorTranslationRepository",
    "ColorService",
    "get_color_service",
    "colors_router",
]
