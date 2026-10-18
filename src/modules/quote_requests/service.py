from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate, ServiceException
from src.modules.configurator_setting.models import ConfiguratorSetting, Currency
from src.modules.configurator_setting.repository import ConfiguratorSettingRepository
from src.modules.configurator_extra.models import BillingType
from src.modules.configurator_extra.repository import ConfiguratorExtraRepository
from src.modules.colors.repository import ColorRepository
from src.modules.rope_products.models import RopeConfiguratorSetting
from src.modules.rope_products.repository import RopeProductRepository, ProductVariantRepository
from src.modules.splice_materials.repository import SpliceMaterialRepository
from src.modules.splice_prices.repository import SplicePriceRuleRepository
from src.modules.splice_types.repository import SpliceTypeRepository
from src.modules.quote_requests.models import (
    ConfiguratorType,
    QuoteRequestStatus,
)
from src.modules.quote_requests.models_dto import (
    QuoteRequestCreate,
    QuoteRopeItemCreate,
    QuoteServiceItemCreate,
    QuoteExtraItemCreate,
    QuoteRequestUpdateDTO,
    QuoteRequestResponseDTO,
    ResolvedRopeItemDTO,
    ResolvedServiceItemDTO,
    ResolvedExtraItemDTO,
    ResolvedEndSpliceDTO,
    QuoteRequestTotalsDTO,
    QuoteRopeItemInsertDTO,
    QuoteServiceItemInsertDTO,
    QuoteExtraItemInsertDTO,
    QuoteRequestInsertDTO,
    QuoteRequestListResponseDTO,
)
from src.modules.quote_requests.repository import (
    QuoteRequestRepository,
    QuoteRopeItemRepository,
    QuoteServiceItemRepository,
    QuoteExtraItemRepository,
)
from src.modules.quote_requests.exception import (
    QuoteRequestNotFound,
    QuoteRequestValidationError,
    ConfiguratorExtraNotFoundForQuote,
    RopeProductNotFoundForQuote,
    RopeVariantNotFoundForQuote,
    ColorNotFoundForQuote,
    ColorNotAllowedForProduct,
    SpliceTypeNotFoundForQuote,
    SpliceMaterialNotFoundForQuote,
    SplicePriceRuleNotFound,
    RopeCannotBeSplicedError,
    SpliceNotAllowedForProductError,
)


class QuoteRequestService:
    def __init__(
        self,
        quote_repo: QuoteRequestRepository,
        rope_item_repo: QuoteRopeItemRepository,
        service_item_repo: QuoteServiceItemRepository,
        extra_item_repo: QuoteExtraItemRepository,
        rope_product_repo: RopeProductRepository,
        variant_repo: ProductVariantRepository,
        color_repo: ColorRepository,
        splice_type_repo: SpliceTypeRepository,
        splice_material_repo: SpliceMaterialRepository,
        splice_price_repo: SplicePriceRuleRepository,
        extra_repo: ConfiguratorExtraRepository,
        configurator_setting_repo: ConfiguratorSettingRepository,
        session: AsyncSession,
    ):
        self.quote_repo = quote_repo
        self.rope_item_repo = rope_item_repo
        self.service_item_repo = service_item_repo
        self.extra_item_repo = extra_item_repo
        self.rope_product_repo = rope_product_repo
        self.variant_repo = variant_repo
        self.color_repo = color_repo
        self.splice_type_repo = splice_type_repo
        self.splice_material_repo = splice_material_repo
        self.splice_price_repo = splice_price_repo
        self.extra_repo = extra_repo
        self.configurator_setting_repo = configurator_setting_repo
        self.session = session

    async def create_quote_request(
        self,
        data: QuoteRequestCreate,
    ) -> QuoteRequestResponseDTO:
        """
        Создание новой заявки с автоматическим формированием снимков (Order Snapshot),
        валидацией совместимости и расчетом стоимости (включая надбавку за срочность и опции).
        """
        # 1. Загрузка глобальных настроек
        setting = await self.configurator_setting_repo.get_settings()
        vat_rate = float(setting.vat_rate) if setting else 0.0
        currency = setting.currency if setting else Currency.EUR

        # 2. Валидация входных позиций
        self._validate_request_items(data, setting)

        locale = data.locale or Language.ENG

        # 3. Разрешение позиций в DTO снимков
        resolved_rope_items = await self._resolve_rope_items(data.rope_items, locale, setting)
        resolved_service_items = await self._resolve_service_items(data.service_items, locale)
        resolved_extra_items = await self._resolve_extra_items(
            data=data,
            rope_items=resolved_rope_items,
            service_items=resolved_service_items,
            locale=locale,
        )

        # 4. Расчет финансовых итогов
        totals = self._calculate_totals(
            rope_items=resolved_rope_items,
            service_items=resolved_service_items,
            extra_items=resolved_extra_items,
            is_urgent=data.is_urgent,
            setting=setting,
        )

        # 5. Генерация уникального номера заявки
        request_number = await self._generate_request_number()

        # 6. Сохранение заявки и дочерних снимков
        try:
            quote_id = await self._save_quote_request(
                data=data,
                request_number=request_number,
                currency=currency,
                vat_rate=vat_rate,
                subtotal=totals.subtotal,
                urgent_surcharge=totals.urgent_surcharge,
                total_price=totals.total_price,
                rope_items=resolved_rope_items,
                service_items=resolved_service_items,
                extra_items=resolved_extra_items,
            )
            await self.session.commit()
        except Exception as err:
            await self.session.rollback()
            logger.exception("Failed to save quote request: %s", err)
            raise ServiceException(f"Failed to create quote request: {err}") from err

        loaded = await self.quote_repo.get_by_id(quote_id, include_relations=True)
        return QuoteRequestResponseDTO.model_validate(loaded)

    def _validate_request_items(
        self,
        data: QuoteRequestCreate,
        setting: Optional[ConfiguratorSetting],
    ) -> None:
        """Валидация наличия и состава позиций заявки для выбранного типа конфигуратора."""
        if not data.rope_items and not data.service_items:
            raise QuoteRequestValidationError("At least one item (rope or service) must be provided.")

        if data.configurator_type == ConfiguratorType.ROPE_WITH_SPLICE:
            if data.service_items:
                raise QuoteRequestValidationError("service_items are not allowed for rope configurator.")
            if not data.rope_items:
                raise QuoteRequestValidationError(
                    "Rope with splice configurator requires at least one rope item."
                )

        if data.configurator_type in (ConfiguratorType.LOOP_ONLY, ConfiguratorType.SPLICE_ONLY):
            if data.rope_items:
                raise QuoteRequestValidationError(
                    f"rope_items are not allowed for {data.configurator_type.value} configurator."
                )
            if not data.service_items:
                raise QuoteRequestValidationError(
                    f"{data.configurator_type.value} configurator requires at least one service item."
                )

        if setting and data.rope_items:
            min_len = float(setting.min_length_m)
            max_len = float(setting.max_length_m)
            for r_item in data.rope_items:
                if r_item.length_m < min_len:
                    raise QuoteRequestValidationError(
                        f"Rope length ({r_item.length_m} m) is less than minimum allowed ({min_len} m)."
                    )
                if r_item.length_m > max_len:
                    raise QuoteRequestValidationError(
                        f"Rope length ({r_item.length_m} m) exceeds maximum allowed ({max_len} m)."
                    )

    async def _resolve_rope_items(
        self,
        items: List[QuoteRopeItemCreate],
        locale: Language,
        setting: Optional[ConfiguratorSetting] = None,
    ) -> List[ResolvedRopeItemDTO]:
        """Разрешение списка конфигураций канатов в DTO снимков."""
        resolved: List[ResolvedRopeItemDTO] = []
        for r_item in items:
            resolved_item = await self._resolve_single_rope_item(r_item, locale, setting)
            resolved.append(resolved_item)
        return resolved

    async def _resolve_single_rope_item(
        self,
        r_item: QuoteRopeItemCreate,
        locale: Language,
        setting: Optional[ConfiguratorSetting] = None,
    ) -> ResolvedRopeItemDTO:
        """Валидация и построение DTO-снимка для отдельной позиции каната."""
        rope_product = await self.rope_product_repo.get_by_product_id(
            r_item.product_id,
            include_relations=True,
        )
        if not rope_product:
            raise RopeProductNotFoundForQuote(
                f"Product with product_id {r_item.product_id} not found."
            )

        variant = await self.variant_repo.get_by_product_and_size(
            product_id=r_item.product_id,
            size_value=r_item.diameter_mm,
        )
        if not variant:
            raise RopeVariantNotFoundForQuote(
                f"Variant with diameter {r_item.diameter_mm} mm not found for product {r_item.product_id}."
            )

        color = await self.color_repo.get_by_id(r_item.color_id)
        if not color:
            raise ColorNotFoundForQuote(f"Color with id {r_item.color_id} not found.")

        self._validate_product_color_compatibility(rope_product, r_item.color_id)

        product_name_snapshot = self._extract_rope_product_name(rope_product, locale)
        color_name_snapshot = color._get_field_with_translation(
            lambda t: t.name, locale
        ) or color.code

        price_per_meter = Decimal(str(variant.price))

        end_a = await self._resolve_rope_end_splice(
            rope_product=rope_product,
            splice_type_id=r_item.end_a_type_id,
            diameter_mm=r_item.diameter_mm,
            quantity=r_item.quantity,
            locale=locale,
        )
        end_b = await self._resolve_rope_end_splice(
            rope_product=rope_product,
            splice_type_id=r_item.end_b_type_id,
            diameter_mm=r_item.diameter_mm,
            quantity=r_item.quantity,
            locale=locale,
        )

        splices_count = (1 if r_item.end_a_type_id else 0) + (1 if r_item.end_b_type_id else 0)
        allowance_m = Decimal("0.0")
        if setting and splices_count > 0:
            allowance_per_splice = (
                Decimal(str(setting.splice_allowance_until_m))
                if Decimal(str(r_item.diameter_mm)) <= Decimal(str(setting.splice_allowance_until_mm))
                else Decimal(str(setting.splice_allowance_over_m))
            )
            allowance_m = Decimal(splices_count) * allowance_per_splice

        effective_length = Decimal(str(r_item.length_m)) + allowance_m
        total_rope_cost = (price_per_meter * effective_length * Decimal(r_item.quantity)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return ResolvedRopeItemDTO(
            product_id=r_item.product_id,
            color_id=r_item.color_id,
            product_name_snapshot=product_name_snapshot,
            color_name_snapshot=color_name_snapshot,
            diameter_mm=r_item.diameter_mm,
            length_m=r_item.length_m,
            quantity=r_item.quantity,
            price_per_meter_snapshot=float(price_per_meter),
            total_rope_cost=float(total_rope_cost),
            end_a_type_id=r_item.end_a_type_id,
            end_a_name_snapshot=end_a.name_snapshot,
            end_a_eye_size_cm=r_item.end_a_eye_size_cm,
            end_a_cost=end_a.cost,
            end_b_type_id=r_item.end_b_type_id,
            end_b_name_snapshot=end_b.name_snapshot,
            end_b_eye_size_cm=r_item.end_b_eye_size_cm,
            end_b_cost=end_b.cost,
        )

    def _validate_product_color_compatibility(self, rope_product: RopeConfiguratorSetting, color_id: int) -> None:
        """Проверка доступности выбранного цвета для каната."""
        colors = rope_product.product.colors if rope_product.product and rope_product.product.colors else []
        assigned_color_ids = [c.color_id for c in colors]
        if assigned_color_ids and color_id not in assigned_color_ids:
            raise ColorNotAllowedForProduct(
                f"Color {color_id} is not available for rope product {rope_product.product_id}."
            )

    def _extract_rope_product_name(self, rope_product: RopeConfiguratorSetting, locale: Language) -> str:
        """Формирование читаемого названия каната для исторического снимка."""
        if rope_product.product and rope_product.product.translations:
            for t in rope_product.product.translations:
                if t.locale == locale.value or t.locale == locale:
                    return t.name
            return rope_product.product.translations[0].name
        if rope_product.construction:
            return rope_product.construction
        if rope_product.material_group:
            name = rope_product.material_group._get_field_with_translation(
                lambda t: t.name, locale
            )
            if name:
                return name
        return f"Rope Product #{rope_product.product_id}"

    async def _resolve_rope_end_splice(
        self,
        rope_product: RopeConfiguratorSetting,
        splice_type_id: Optional[int],
        diameter_mm: float,
        quantity: int,
        locale: Language,
    ) -> ResolvedEndSpliceDTO:
        """Валидация законцовки каната и расчет стоимости с формированием DTO."""
        if splice_type_id is None:
            return ResolvedEndSpliceDTO(name_snapshot=None, cost=0.0)

        if not rope_product.can_be_spliced:
            raise RopeCannotBeSplicedError(
                f"Rope product {rope_product.product_id} does not support splicing."
            )

        splice_type = await self.splice_type_repo.get_by_id(splice_type_id)
        if not splice_type:
            raise SpliceTypeNotFoundForQuote(f"SpliceType with id {splice_type_id} not found.")

        splices = rope_product.product.allowed_splices if rope_product.product and rope_product.product.allowed_splices else []
        allowed_ids = [s.splice_type_id for s in splices]
        if allowed_ids and splice_type_id not in allowed_ids:
            raise SpliceNotAllowedForProductError(
                f"Splice type {splice_type_id} is not allowed for rope product {rope_product.product_id}."
            )

        unit_price = await self.splice_price_repo.get_price(
            material_id=rope_product.splice_material_id,
            type_id=splice_type_id,
            diameter=diameter_mm,
        )
        if unit_price is None:
            raise SplicePriceRuleNotFound(
                f"No pricing rule found for splice type {splice_type_id}, "
                f"material {rope_product.splice_material_id}, diameter {diameter_mm} mm."
            )

        name_snapshot = splice_type._get_field_with_translation(
            lambda t: t.name, locale
        ) or splice_type.code
        # quantity — количество готовых изделий, а не отдельных концов.
        # Стоимость выбранного типа сращивания для этого конца рассчитывается
        # с учётом количества изделий.
        unit_price_dec = Decimal(str(unit_price))
        cost = (unit_price_dec * Decimal(quantity)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return ResolvedEndSpliceDTO(name_snapshot=name_snapshot, cost=float(cost))

    async def _resolve_service_items(
        self,
        items: List[QuoteServiceItemCreate],
        locale: Language,
    ) -> List[ResolvedServiceItemDTO]:
        """Разрешение списка услуг в DTO снимков."""
        resolved: List[ResolvedServiceItemDTO] = []
        for s_item in items:
            resolved_item = await self._resolve_single_service_item(s_item, locale)
            resolved.append(resolved_item)
        return resolved

    async def _resolve_single_service_item(
        self,
        s_item: QuoteServiceItemCreate,
        locale: Language,
    ) -> ResolvedServiceItemDTO:
        """Валидация и построение DTO-снимка для отдельной услуги (петля/сращивание)."""
        splice_type = await self.splice_type_repo.get_by_id(s_item.splice_type_id)
        if not splice_type:
            raise SpliceTypeNotFoundForQuote(
                f"SpliceType with id {s_item.splice_type_id} not found."
            )

        splice_material = await self.splice_material_repo.get_by_id(s_item.splice_material_id)
        if not splice_material:
            raise SpliceMaterialNotFoundForQuote(
                f"SpliceMaterial with id {s_item.splice_material_id} not found."
            )

        unit_price = await self.splice_price_repo.get_price(
            material_id=s_item.splice_material_id,
            type_id=s_item.splice_type_id,
            diameter=float(s_item.diameter_mm),
        )
        if unit_price is None:
            raise SplicePriceRuleNotFound(
                f"No pricing rule found for service {s_item.splice_type_id}, "
                f"material {s_item.splice_material_id}, diameter {s_item.diameter_mm} mm."
            )

        service_name_snapshot = splice_type._get_field_with_translation(
            lambda t: t.name, locale
        ) or splice_type.code
        material_name_snapshot = splice_material.name
        unit_price_dec = Decimal(str(unit_price))
        total_cost = (unit_price_dec * Decimal(s_item.quantity)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return ResolvedServiceItemDTO(
            splice_type_id=s_item.splice_type_id,
            splice_material_id=s_item.splice_material_id,
            service_name_snapshot=service_name_snapshot,
            material_name_snapshot=material_name_snapshot,
            diameter_mm=s_item.diameter_mm,
            eye_size_cm=s_item.eye_size_cm,
            quantity=s_item.quantity,
            unit_price_snapshot=float(unit_price_dec),
            total_cost=float(total_cost),
        )

    async def _resolve_extra_items(
        self,
        data: QuoteRequestCreate,
        rope_items: List[ResolvedRopeItemDTO],
        service_items: List[ResolvedServiceItemDTO],
        locale: Language,
    ) -> List[ResolvedExtraItemDTO]:
        """Разрешение дополнительных опций конфигуратора."""
        seen_ids = set()
        unique_requests: List[QuoteExtraItemCreate] = []
        for it in data.extra_items:
            if it.extra_id not in seen_ids:
                seen_ids.add(it.extra_id)
                unique_requests.append(it)

        resolved_extras: List[ResolvedExtraItemDTO] = []
        for req in unique_requests:
            extra = await self.extra_repo.get_by_id(req.extra_id)
            if not extra:
                raise ConfiguratorExtraNotFoundForQuote(
                    f"ConfiguratorExtra with id {req.extra_id} not found."
                )
            if not extra.is_active:
                raise QuoteRequestValidationError(
                    f"ConfiguratorExtra with id {req.extra_id} is inactive."
                )

            name_snapshot = extra._get_field_with_translation(
                lambda t: t.name, locale
            ) or extra.code
            unit_price_dec = Decimal(str(extra.price))
            billing_type = extra.billing_type

            if billing_type == BillingType.FIXED:
                quantity = 1
                total_cost = unit_price_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            elif billing_type == BillingType.PER_ITEM:
                if data.configurator_type == ConfiguratorType.ROPE_WITH_SPLICE:
                    order_items_qty = sum(r.quantity for r in rope_items)
                else:
                    order_items_qty = sum(s.quantity for s in service_items)

                quantity = max(1, order_items_qty)
                total_cost = (unit_price_dec * Decimal(quantity)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

            elif billing_type == BillingType.PER_METER:
                if data.configurator_type != ConfiguratorType.ROPE_WITH_SPLICE:
                    raise QuoteRequestValidationError(
                        f"Extra '{extra.code}' with per-meter billing cannot be applied to {data.configurator_type.value} orders."
                    )
                total_length_dec = sum(Decimal(str(r.length_m)) * Decimal(r.quantity) for r in rope_items)
                if total_length_dec <= 0:
                    raise QuoteRequestValidationError(
                        f"Extra '{extra.code}' with per-meter billing requires rope items with length."
                    )
                quantity = max(1, int(round(float(total_length_dec))))
                total_cost = (unit_price_dec * total_length_dec).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

            else:
                quantity = 1
                total_cost = unit_price_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            resolved_extras.append(
                ResolvedExtraItemDTO(
                    extra_id=extra.id,
                    name_snapshot=name_snapshot,
                    billing_type_snapshot=billing_type.value,
                    quantity=quantity,
                    unit_price_snapshot=float(unit_price_dec),
                    total_cost=float(total_cost),
                )
            )

        return resolved_extras

    def _calculate_totals(
        self,
        rope_items: List[ResolvedRopeItemDTO],
        service_items: List[ResolvedServiceItemDTO],
        extra_items: List[ResolvedExtraItemDTO],
        is_urgent: bool,
        setting: Optional[ConfiguratorSetting],
    ) -> QuoteRequestTotalsDTO:
        """Расчет общей стоимости заявки, включая надбавку за срочность и доп. опции."""
        subtotal_dec = (
            sum(Decimal(str(r.total_cost)) for r in rope_items)
            + sum(Decimal(str(s.total_cost)) for s in service_items)
            + sum(Decimal(str(e.total_cost)) for e in extra_items)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        urgent_surcharge_dec = Decimal("0.00")
        if is_urgent:
            # Считаем общее количество сращиваний с учётом quantity:
            # для канатных изделий учитываются обработанные концы каждого изделия,
            # для отдельных услуг — количество заказанных услуг.
            # Это количество используется для проверки лимита срочной обработки
            # и расчёта надбавки за срочность.
            total_splices = sum(r.splices_count for r in rope_items) + sum(s.splices_count for s in service_items)
            if setting and total_splices > setting.urgent_max_splices:
                raise QuoteRequestValidationError(
                    f"Urgent processing exceeds maximum allowed splices ({setting.urgent_max_splices}), requested {total_splices}."
                )
            surcharge_rate_dec = (
                Decimal(str(setting.urgent_surcharge_per_splice))
                if setting
                else Decimal("10.00")
            )
            urgent_surcharge_dec = (Decimal(total_splices) * surcharge_rate_dec).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        total_price_dec = (subtotal_dec + urgent_surcharge_dec).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return QuoteRequestTotalsDTO(
            subtotal=float(subtotal_dec),
            urgent_surcharge=float(urgent_surcharge_dec),
            total_price=float(total_price_dec),
        )

    async def _save_quote_request(
        self,
        data: QuoteRequestCreate,
        request_number: str,
        currency: Currency,
        vat_rate: float,
        subtotal: float,
        urgent_surcharge: float,
        total_price: float,
        rope_items: List[ResolvedRopeItemDTO],
        service_items: List[ResolvedServiceItemDTO],
        extra_items: List[ResolvedExtraItemDTO],
    ) -> int:
        """Сохранение сущности QuoteRequest и ее дочерних снимков с использованием DTO."""
        quote_insert_dto = QuoteRequestInsertDTO(
            request_number=request_number,
            configurator_type=data.configurator_type,
            name=data.name,
            email=str(data.email),
            phone=data.phone,
            comment=data.comment,
            currency=currency,
            subtotal=subtotal,
            urgent_surcharge=urgent_surcharge,
            total_price=total_price,
            vat_rate=vat_rate,
            is_urgent=data.is_urgent,
            status=QuoteRequestStatus.NEW,
        )
        quote_request = await self.quote_repo.add_quote_request(quote_insert_dto)
        await self.session.flush()

        for r_dto in rope_items:
            rope_item_dto = QuoteRopeItemInsertDTO(
                quote_request_id=quote_request.id,
                product_id=r_dto.product_id,
                color_id=r_dto.color_id,
                product_name_snapshot=r_dto.product_name_snapshot,
                color_name_snapshot=r_dto.color_name_snapshot,
                diameter_mm=r_dto.diameter_mm,
                length_m=r_dto.length_m,
                quantity=r_dto.quantity,
                price_per_meter_snapshot=r_dto.price_per_meter_snapshot,
                total_rope_cost=r_dto.total_rope_cost,
                end_a_type_id=r_dto.end_a_type_id,
                end_a_name_snapshot=r_dto.end_a_name_snapshot,
                end_a_eye_size_cm=r_dto.end_a_eye_size_cm,
                end_a_cost=r_dto.end_a_cost,
                end_b_type_id=r_dto.end_b_type_id,
                end_b_name_snapshot=r_dto.end_b_name_snapshot,
                end_b_eye_size_cm=r_dto.end_b_eye_size_cm,
                end_b_cost=r_dto.end_b_cost,
            )
            await self.rope_item_repo.add_item(rope_item_dto)

        for s_dto in service_items:
            service_item_dto = QuoteServiceItemInsertDTO(
                quote_request_id=quote_request.id,
                splice_type_id=s_dto.splice_type_id,
                splice_material_id=s_dto.splice_material_id,
                service_name_snapshot=s_dto.service_name_snapshot,
                material_name_snapshot=s_dto.material_name_snapshot,
                diameter_mm=s_dto.diameter_mm,
                eye_size_cm=s_dto.eye_size_cm,
                quantity=s_dto.quantity,
                unit_price_snapshot=s_dto.unit_price_snapshot,
                total_cost=s_dto.total_cost,
            )
            await self.service_item_repo.add_item(service_item_dto)

        for e_dto in extra_items:
            extra_item_dto = QuoteExtraItemInsertDTO(
                quote_request_id=quote_request.id,
                extra_id=e_dto.extra_id,
                name_snapshot=e_dto.name_snapshot,
                billing_type_snapshot=e_dto.billing_type_snapshot,
                quantity=e_dto.quantity,
                unit_price_snapshot=e_dto.unit_price_snapshot,
                total_cost=e_dto.total_cost,
            )
            await self.extra_item_repo.add_item(extra_item_dto)

        return quote_request.id

    async def _generate_request_number(self) -> str:
        """Генерация уникального бизнес-номера заявки формата RPL-YYYY-NNNN."""
        current_year = datetime.now(timezone.utc).year
        seq_num = await self.quote_repo.get_next_request_number_seq()

        return f"RPL-{current_year}-{seq_num:04d}"

    async def get_quote_request_by_id(self, request_id: int) -> QuoteRequestResponseDTO:
        item = await self.quote_repo.get_by_id(request_id, include_relations=True)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")
        return QuoteRequestResponseDTO.model_validate(item)

    async def get_by_id(self, request_id: int) -> QuoteRequestResponseDTO:
        return await self.get_quote_request_by_id(request_id)


    async def get_by_request_number(self, request_number: str) -> QuoteRequestResponseDTO:
        item = await self.quote_repo.get_by_request_number(request_number, include_relations=True)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with request_number '{request_number}' not found.")
        return QuoteRequestResponseDTO.model_validate(item)

    async def list_quote_requests(
        self,
        status: Optional[QuoteRequestStatus] = None,
        configurator_type: Optional[ConfiguratorType] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        request_number: Optional[str] = None,
        is_urgent: Optional[bool] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 50,
    ) -> QuoteRequestListResponseDTO:
        items = await self.quote_repo.get_all(
            status=status,
            configurator_type=configurator_type,
            name=name,
            email=email,
            phone=phone,
            request_number=request_number,
            is_urgent=is_urgent,
            created_from=created_from,
            created_to=created_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit,
        )
        total = await self.quote_repo.count_all(
            status=status,
            configurator_type=configurator_type,
            name=name,
            email=email,
            phone=phone,
            request_number=request_number,
            is_urgent=is_urgent,
            created_from=created_from,
            created_to=created_to,
            search=search,
        )
        return QuoteRequestListResponseDTO(
            items=[QuoteRequestResponseDTO.model_validate(i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def update_quote_request(
        self,
        request_id: int,
        data: QuoteRequestUpdateDTO,
    ) -> QuoteRequestResponseDTO:
        item = await self.quote_repo.get_by_id(request_id)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("Did not transmit data")

        await self.quote_repo.update_quote_request(request_id, update_dict)
        await self.session.commit()

        updated = await self.quote_repo.get_by_id(request_id, include_relations=True)
        return QuoteRequestResponseDTO.model_validate(updated)

    async def update_quote_request_status(
        self,
        request_id: int,
        status: QuoteRequestStatus,
    ) -> QuoteRequestResponseDTO:
        item = await self.quote_repo.get_by_id(request_id)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")

        await self.quote_repo.update_quote_request(request_id, {"status": status})
        await self.session.commit()

        updated = await self.quote_repo.get_by_id(request_id, include_relations=True)
        return QuoteRequestResponseDTO.model_validate(updated)

    async def delete_quote_request(self, request_id: int) -> None:
        item = await self.quote_repo.get_by_id(request_id)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")

        await self.quote_repo.delete_quote_request(request_id)
        await self.session.commit()
