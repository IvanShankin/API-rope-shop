from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.quote_requests.models import ConfiguratorType
from src.modules.configurator_setting.models_dto import ConfiguratorSettingResponseDTO
from src.modules.configurator_extra.models import ConfiguratorExtra, BillingType
from src.modules.configurator_extra.models_dto import ConfiguratorExtraLocalizedResponseDTO
from src.modules.splice_materials.models_dto import SpliceMaterialResponseDTO
from src.modules.splice_types.models import SpliceType, SpliceCategory
from src.modules.splice_types.models_dto import SpliceTypeLocalizedResponseDTO
from src.modules.splice_prices.models_dto import SplicePriceRuleResponseDTO
from src.modules.colors.models_dto import ColorLocalizedResponseDTO
from src.modules.rope_products.models import RopeConfiguratorSetting
from src.modules.rope_products.models_dto import ProductVariantResponseDTO
from src.modules.rope_product_color.models_dto import ProductColorLocalizedResponseDTO
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceLocalizedResponseDTO
from src.modules.configurators.models_dto import (
    ConfiguratorDataResponseDTO,
    ConfiguratorRopeProductResponseDTO,
    SplicePriceCalculationResponseDTO,
)
from src.modules.configurators.repository import ConfiguratorRepository
from src.modules.splice_prices.exception import SplicePriceRuleNotFound
from src.modules.splice_prices.repository import SplicePriceRuleRepository


class ConfiguratorService:
    def __init__(
        self,
        repo: ConfiguratorRepository,
        session: AsyncSession,
    ):
        self.repo = repo
        self.session = session

    async def get_configurator_data(
        self,
        configurator_type: Optional[ConfiguratorType] = None,
        locale: Language = Language.ENG,
    ) -> ConfiguratorDataResponseDTO:
        """
        Получение агрегированных данных для конфигураторов.
        При указании configurator_type возвращает целевой набор сущностей и правил для выбранного сценария:
        - ROPE_WITH_SPLICE: канат + варианты + цвета + разрешенные заделки, матрица цен, настройки и все доп. опции.
        - LOOP_ONLY: только услуги петель (LOOP), матрица цен на петли, тарифные группы материалов и применимые доп. опции.
        - SPLICE_ONLY: только услуги сращиваний (SPLICE), матрица цен, тарифные группы материалов и применимые доп. опции.
        - None: полный сводный пакет для всех трех конфигураторов.
        """
        # 1. Системные настройки
        setting_orm = await self.repo.get_setting()
        settings_dto = ConfiguratorSettingResponseDTO.model_validate(setting_orm) if setting_orm else None

        # 2. Дополнительные опции
        extras_orm = await self.repo.get_extras(is_active=True)
        if configurator_type in (ConfiguratorType.LOOP_ONLY, ConfiguratorType.SPLICE_ONLY):
            # Для услуг без покупки каната опции с пометовой тарификацией неприменимы
            extras_orm = [e for e in extras_orm if e.billing_type != BillingType.PER_METER]
        extras_dto = [self._localize_extra(e, locale) for e in extras_orm]

        # 3. Тарифные группы материалов заделок
        materials_orm = await self.repo.get_splice_materials()
        materials_dto = [SpliceMaterialResponseDTO.model_validate(m) for m in materials_orm]

        # 4. Категория заделок по типу конфигуратора
        target_category: Optional[SpliceCategory] = None
        if configurator_type == ConfiguratorType.LOOP_ONLY:
            target_category = SpliceCategory.LOOP
        elif configurator_type == ConfiguratorType.SPLICE_ONLY:
            target_category = SpliceCategory.SPLICE

        # 5. Услуги заделок
        types_orm = await self.repo.get_splice_types(category=target_category, is_active=True)
        types_dto = [self._localize_splice_type(t, locale) for t in types_orm]

        # 6. Матрица цен на заделки
        rules_orm = await self.repo.get_splice_price_rules(category=target_category, is_active=True)
        rules_dto = [SplicePriceRuleResponseDTO.model_validate(r) for r in rules_orm]

        # 7. Каталог канатов (только для каната со сплайсом или при общем запросе)
        rope_products_dto: Optional[List[ConfiguratorRopeProductResponseDTO]] = None
        if configurator_type is None or configurator_type == ConfiguratorType.ROPE_WITH_SPLICE:
            ropes_orm = await self.repo.get_rope_products()
            rope_products_dto = [self._localize_rope_product(r, locale) for r in ropes_orm]

        return ConfiguratorDataResponseDTO(
            configurator_type=configurator_type,
            locale=locale,
            settings=settings_dto,
            extras=extras_dto,
            splice_materials=materials_dto,
            splice_types=types_dto,
            splice_price_rules=rules_dto,
            rope_products=rope_products_dto,
        )

    def _localize_extra(
        self,
        extra: ConfiguratorExtra,
        locale: Language,
    ) -> ConfiguratorExtraLocalizedResponseDTO:
        """Локализация названия и описания дополнительной опции."""
        name = extra._get_field_with_translation(lambda t: t.name, locale) or extra.code
        description = extra._get_field_with_translation(lambda t: t.description, locale)
        return ConfiguratorExtraLocalizedResponseDTO(
            id=extra.id,
            code=extra.code,
            price=float(extra.price),
            currency=extra.currency,
            billing_type=extra.billing_type,
            index=extra.index,
            is_active=extra.is_active,
            name=name,
            description=description,
            created_at=extra.created_at,
            updated_at=extra.updated_at,
        )

    def _localize_splice_type(
        self,
        splice_type: SpliceType,
        locale: Language,
    ) -> SpliceTypeLocalizedResponseDTO:
        """Локализация названия и описания типа заделки."""
        name = splice_type._get_field_with_translation(lambda t: t.name, locale) or splice_type.code
        description = splice_type._get_field_with_translation(lambda t: t.description, locale)
        return SpliceTypeLocalizedResponseDTO(
            id=splice_type.id,
            created_at=splice_type.created_at,
            updated_at=splice_type.updated_at,
            code=splice_type.code,
            category=splice_type.category,
            visual_type=splice_type.visual_type,
            image_url=splice_type.image_url,
            index=splice_type.index,
            is_active=splice_type.is_active,
            name=name,
            description=description,
        )

    def _localize_rope_product(
        self,
        rope: RopeConfiguratorSetting,
        locale: Language,
    ) -> ConfiguratorRopeProductResponseDTO:
        """Локализация характеристик каната, связанных цветов и разрешенных заделок."""
        mat_group_name = None
        if rope.material_group and rope.material_group.is_active:
            mat_group_name = rope.material_group._get_field_with_translation(
                lambda t: t.name, locale
            )

        product = rope.product
        product_name = None
        product_slug = None
        product_main_image_url = None
        product_subtitle = None

        if product:
            product_slug = product.slug
            product_main_image_url = product.main_image_url
            product_name = product._get_field_with_translation(
                lambda t: t.name,
                locale,
                fallback=Language.ENG,
            )
            product_subtitle = product._get_field_with_translation(
                lambda t: t.subtitle,
                locale,
                fallback=Language.ENG,
            )

        variants_list = product.variants if product and product.variants else []
        colors_list = product.colors if product and product.colors else []
        splices_list = product.allowed_splices if product and product.allowed_splices else []

        variants_dto = [
            ProductVariantResponseDTO.model_validate(v)
            for v in variants_list
            if v.is_active
        ]

        colors_dto: List[ProductColorLocalizedResponseDTO] = []
        for rc in colors_list:
            if rc.color and rc.color.is_active:
                c_name = rc.color._get_field_with_translation(
                    lambda t: t.name, locale
                ) or rc.color.code
                color_loc = ColorLocalizedResponseDTO(
                    id=rc.color.id,
                    code=rc.color.code,
                    hex=rc.color.hex,
                    index=rc.color.index,
                    is_active=rc.color.is_active,
                    name=c_name,
                )
                colors_dto.append(
                    ProductColorLocalizedResponseDTO(
                        id=rc.id,
                        product_id=rc.product_id,
                        color_id=rc.color_id,
                        index=rc.index,
                        color=color_loc,
                    )
                )

        splices_dto: List[RopeAllowedSpliceLocalizedResponseDTO] = []
        for rs in splices_list:
            if rs.splice_type and rs.splice_type.is_active:
                st_loc = self._localize_splice_type(rs.splice_type, locale)
                splices_dto.append(
                    RopeAllowedSpliceLocalizedResponseDTO(
                        product_id=rs.product_id,
                        splice_type_id=rs.splice_type_id,
                        splice_type=st_loc,
                    )
                )

        splice_material_dto = (
            SpliceMaterialResponseDTO.model_validate(rope.splice_material)
            if rope.splice_material
            else None
        )

        return ConfiguratorRopeProductResponseDTO(
            product_id=rope.product_id,
            name=product_name,
            slug=product_slug,
            main_image_url=product_main_image_url,
            subtitle=product_subtitle,
            material_group_id=rope.material_group_id,
            material_group_name=mat_group_name,
            splice_material_id=rope.splice_material_id,
            construction=rope.construction,
            core_description=rope.core_description,
            cover_description=rope.cover_description,
            can_be_spliced=rope.can_be_spliced,
            variants=variants_dto,
            colors=colors_dto,
            allowed_splices=splices_dto,
            splice_material=splice_material_dto,
        )

    async def calculate_splice_price(
        self,
        material_id: int,
        splice_type_id: int,
        diameter_mm: float,
    ) -> SplicePriceCalculationResponseDTO:
        """Точечный расчет цены заделки по правилам матрицы цен."""
        price_repo = SplicePriceRuleRepository(self.session)
        price = await price_repo.get_price(
            material_id=material_id,
            type_id=splice_type_id,
            diameter=diameter_mm,
        )
        if price is None:
            raise SplicePriceRuleNotFound(
                f"No splice price rule found for material_id={material_id}, "
                f"splice_type_id={splice_type_id}, diameter={diameter_mm}mm"
            )
        return SplicePriceCalculationResponseDTO(
            price=float(price),
            currency="EUR",
            material_id=material_id,
            splice_type_id=splice_type_id,
            diameter_mm=diameter_mm,
        )

