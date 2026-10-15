from src.modules.product_specification.models import (
    ProductSpecification,
    ProductSpecificationTranslation,
)
from src.modules.product_specification.repository import (
    ProductSpecificationRepository,
    ProductSpecificationTranslationRepository,
)
from src.modules.product_specification.service import ProductSpecificationService
from src.modules.product_specification.depends import get_product_specification_service
from src.modules.product_specification.views import router as product_specifications_router

__all__ = [
    "ProductSpecification",
    "ProductSpecificationTranslation",
    "ProductSpecificationRepository",
    "ProductSpecificationTranslationRepository",
    "ProductSpecificationService",
    "get_product_specification_service",
    "product_specifications_router",
]
