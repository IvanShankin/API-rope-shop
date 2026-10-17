from typing import List, Optional
from pydantic import BaseModel

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.database_model import Language
from src.modules.quote_requests.models import ConfiguratorType
from src.modules.configurator_setting.models_dto import ConfiguratorSettingResponseDTO
from src.modules.configurator_extra.models_dto import ConfiguratorExtraLocalizedResponseDTO
from src.modules.splice_materials.models_dto import SpliceMaterialResponseDTO
from src.modules.splice_types.models_dto import SpliceTypeLocalizedResponseDTO
from src.modules.splice_prices.models_dto import SplicePriceRuleResponseDTO
from src.modules.rope_products.models_dto import ProductVariantResponseDTO
from src.modules.rope_product_color.models_dto import ProductColorLocalizedResponseDTO
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceLocalizedResponseDTO


class ConfiguratorRopeProductResponseDTO(ORMDTO):
    """Канат с вариантами диаметров, цветами и разрешёнными заделками для конфигуратора."""
    product_id: int
    name: Optional[str] = None
    slug: Optional[str] = None
    main_image_url: Optional[str] = None
    subtitle: Optional[str] = None
    material_group_id: int
    material_group_name: Optional[str] = None
    splice_material_id: int
    construction: Optional[str] = None
    core_description: Optional[str] = None
    cover_description: Optional[str] = None
    can_be_spliced: bool = True
    variants: List[ProductVariantResponseDTO] = []
    colors: List[ProductColorLocalizedResponseDTO] = []
    allowed_splices: List[RopeAllowedSpliceLocalizedResponseDTO] = []
    splice_material: Optional[SpliceMaterialResponseDTO] = None


class ConfiguratorDataResponseDTO(BaseModel):
    """Агрегированный ответ с данными и настройками для работы конфигуратора."""
    configurator_type: Optional[ConfiguratorType] = None
    locale: Language = Language.ENG
    settings: Optional[ConfiguratorSettingResponseDTO] = None
    extras: List[ConfiguratorExtraLocalizedResponseDTO] = []
    splice_materials: List[SpliceMaterialResponseDTO] = []
    splice_types: List[SpliceTypeLocalizedResponseDTO] = []
    splice_price_rules: List[SplicePriceRuleResponseDTO] = []
    rope_products: Optional[List[ConfiguratorRopeProductResponseDTO]] = None
