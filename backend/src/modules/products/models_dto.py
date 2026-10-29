from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO, PaginatedResponse
from src.modules.products.models import PriceUnit, ProductType


# ===================== Translation DTOs =====================


class ProductTranslationBase(BaseModel):
    locale: Language
    name: str = Field(..., min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class ProductTranslationCreate(ProductTranslationBase):
    pass


class ProductTranslationInsert(ProductTranslationCreate):
    product_id: int


class ProductTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class ProductTranslationResponseDTO(ProductTranslationBase, ORMDTO):
    id: int
    product_id: int


# ===================== Product Base / Create / Update DTOs =====================


class ProductBase(BaseModel):
    category_id: int = Field(..., gt=0)
    slug: str = Field(..., min_length=1, max_length=150)
    product_type: ProductType = ProductType.ROPE
    price_unit: PriceUnit = PriceUnit.METER
    has_configurator: bool = False
    construction_type: Optional[str] = Field(None, max_length=50)
    index: int = Field(..., ge=0)
    is_active: bool = True


class ProductCreate(BaseModel):
    category_id: int = Field(..., gt=0, description="Category ID this product belongs to")
    slug: str = Field(..., min_length=1, max_length=150, description="Unique human-readable slug")
    product_type: ProductType = Field(
        ProductType.ROPE,
        description="Type of product (rope, finished_product, hardware)",
    )
    price_unit: PriceUnit = Field(
        PriceUnit.METER,
        description="Pricing unit (meter, piece, set)",
    )
    has_configurator: bool = Field(
        False,
        description="Whether this product has a configurator",
    )
    construction_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Construction type for catalog filters",
    )
    index: Optional[int] = Field(
        None,
        ge=0,
        description="Optional position index; if not provided, max_index + 1 will be used",
    )
    is_active: bool = True
    translations: List[ProductTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required when creating a Product",
    )


class ProductUpdate(BaseModel):
    category_id: Optional[int] = Field(None, gt=0)
    slug: Optional[str] = Field(None, min_length=1, max_length=150)
    product_type: Optional[ProductType] = None
    price_unit: Optional[PriceUnit] = None
    has_configurator: Optional[bool] = None
    construction_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None



class ProductUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


# ===================== Related Module DTOs =====================

from src.modules.product_application.models_dto import (  # noqa: E402
    ProductApplicationLocalizedResponseDTO,
    ProductApplicationResponseDTO,
    ProductAssignedApplicationResponseDTO,
)
from src.modules.product_images.models_dto import ProductImageResponseDTO  # noqa: E402
from src.modules.product_specification.models_dto import (  # noqa: E402
    ProductSpecificationLocalizedResponseDTO,
    ProductSpecificationResponseDTO,
)
from src.modules.rope_product_color.models_dto import (  # noqa: E402
    ProductColorLocalizedResponseDTO,
    ProductColorResponseDTO,
)
from src.modules.rope_products.models_dto import ProductVariantResponseDTO  # noqa: E402


# ===================== Response DTOs =====================


class ProductResponseDTO(ProductBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    translations: List[ProductTranslationResponseDTO] = []
    main_image_url: Optional[str] = None
    price_from: Optional[float] = None
    size_min: Optional[float] = None
    size_max: Optional[float] = None
    variants_count: int = 0
    images: List[ProductImageResponseDTO] = []
    specifications: List[ProductSpecificationResponseDTO] = []
    assigned_applications: List[ProductAssignedApplicationResponseDTO] = []
    applications: List[ProductApplicationResponseDTO] = []
    variants: List[ProductVariantResponseDTO] = []
    colors: List[ProductColorResponseDTO] = []


class ProductLocalizedResponseDTO(ORMDTO):
    id: int
    category_id: int
    slug: str
    product_type: str
    price_unit: str = "meter"
    has_configurator: bool = False
    construction_type: Optional[str] = None
    index: int
    is_active: bool
    name: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    main_image_url: Optional[str] = None
    price_from: Optional[float] = None
    size_min: Optional[float] = None
    size_max: Optional[float] = None
    variants_count: int = 0
    images: List[ProductImageResponseDTO] = []
    specifications: List[ProductSpecificationLocalizedResponseDTO] = []
    applications: List[ProductApplicationLocalizedResponseDTO] = []
    variants: List[ProductVariantResponseDTO] = []
    colors: List[ProductColorLocalizedResponseDTO] = []
    created_at: datetime
    updated_at: datetime


class ProductListResponseDTO(PaginatedResponse[ProductLocalizedResponseDTO]):
    """Ответ со списком товаров и метаданными пагинации."""
    pass


class ProductDetailResponseDTO(ORMDTO):
    """Единая схема детального ответа товара с опциональной локализацией и полными переводами."""
    id: int
    category_id: Optional[int] = None
    slug: Optional[str] = None
    product_type: str = "rope"
    price_unit: str = "meter"
    has_configurator: bool = False
    construction_type: Optional[str] = None
    index: int = 0
    is_active: bool = True

    name: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None

    main_image_url: Optional[str] = None
    price_from: Optional[float] = None
    size_min: Optional[float] = None
    size_max: Optional[float] = None
    variants_count: int = 0

    translations: List[ProductTranslationResponseDTO] = []
    images: List[ProductImageResponseDTO] = []
    specifications: List[Union[ProductSpecificationLocalizedResponseDTO, ProductSpecificationResponseDTO]] = []
    assigned_applications: List[ProductAssignedApplicationResponseDTO] = []
    applications: List[Union[ProductApplicationLocalizedResponseDTO, ProductApplicationResponseDTO]] = []
    variants: List[ProductVariantResponseDTO] = []
    colors: List[Union[ProductColorLocalizedResponseDTO, ProductColorResponseDTO]] = []
    created_at: datetime
    updated_at: datetime


# ===================== Catalog Filters DTOs =====================


CONSTRUCTION_NAMES = {
    "hollow": {
        Language.GER: "Hohlgeflecht",
        Language.ENG: "Hollow braid",
        Language.RUS: "Полое плетение (Hohlgeflecht)",
    },
    "hm_core": {
        Language.GER: "Kern Dyneema/Vectran + Mantel",
        Language.ENG: "Dyneema/Vectran core + cover",
        Language.RUS: "Сердечник Dyneema/Vectran + оплётка",
    },
    "polyester_core": {
        Language.GER: "Kern Polyester + Mantel",
        Language.ENG: "Polyester core + cover",
        Language.RUS: "Сердечник полиэстер + оплётка",
    },
    "none": {
        Language.GER: "Beschläge & Zubehör",
        Language.ENG: "Hardware & Rigging",
        Language.RUS: "Фурнитура и такелаж",
    },
}


class FilterMaterialDTO(BaseModel):
    id: int
    code: str
    name: str


class FilterConstructionDTO(BaseModel):
    code: str
    name: str


class FilterApplicationDTO(BaseModel):
    id: int
    code: str
    name: str


class FilterSizeRangeDTO(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class CatalogFiltersResponseDTO(BaseModel):
    materials: List[FilterMaterialDTO] = []
    constructions: List[FilterConstructionDTO] = []
    applications: List[FilterApplicationDTO] = []
    size_range: FilterSizeRangeDTO
