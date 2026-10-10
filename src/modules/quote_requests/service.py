from typing import List, Optional, Tuple
from datetime import datetime
import random
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.configurator.models import ConfiguratorSetting, Currency
from src.modules.colors.repository import ColorRepository
from src.modules.rope_products.models import RopeProduct
from src.modules.rope_products.repository import RopeProductRepository, RopeVariantRepository
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
    QuoteRequestUpdateDTO,
    QuoteRequestResponseDTO,
    ResolvedRopeItemDTO,
    ResolvedServiceItemDTO,
    ResolvedEndSpliceDTO,
    QuoteRequestTotalsDTO,
    QuoteRopeItemInsertDTO,
    QuoteServiceItemInsertDTO,
    QuoteRequestInsertDTO,
)
from src.modules.quote_requests.repository import (
    QuoteRequestRepository,
    QuoteRopeItemRepository,
    QuoteServiceItemRepository,
)
from src.modules.quote_requests.exception import (
    QuoteRequestNotFound,
    QuoteRequestValidationError,
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
        rope_product_repo: RopeProductRepository,
        variant_repo: RopeVariantRepository,
        color_repo: ColorRepository,
        splice_type_repo: SpliceTypeRepository,
        splice_material_repo: SpliceMaterialRepository,
        splice_price_repo: SplicePriceRuleRepository,
        session: AsyncSession,
    ):
        self.quote_repo = quote_repo
        self.rope_item_repo = rope_item_repo
        self.service_item_repo = service_item_repo
        self.rope_product_repo = rope_product_repo
        self.variant_repo = variant_repo
        self.color_repo = color_repo
        self.splice_type_repo = splice_type_repo
        self.splice_material_repo = splice_material_repo
        self.splice_price_repo = splice_price_repo
        self.session = session

    async def create_quote_request(
        self,
        data: QuoteRequestCreate,
    ) -> QuoteRequestResponseDTO:
        """
        Создание новой заявки с автоматическим формированием снимков (Order Snapshot),
        валидацией связанных сущностей каталога и расчетом финальной стоимости.
        """
        # 1. Валидация входных позиций
        self._validate_request_items(data)

        locale = data.locale or Language.ENG

        # 2. Получение настроек конфигуратора
        currency, vat_rate, urgent_surcharge_per_splice = await self._get_configurator_setting()

        # 3. Разрешение позиций канатов и услуг в DTO-снимки
        resolved_rope_items = await self._resolve_rope_items(data.rope_items, locale)
        resolved_service_items = await self._resolve_service_items(data.service_items, locale)

        # 4. Расчет итогов заказа
        totals = self._calculate_totals(
            rope_items=resolved_rope_items,
            service_items=resolved_service_items,
            is_urgent=data.is_urgent,
            urgent_surcharge_per_splice=urgent_surcharge_per_splice,
        )

        # 5. Генерация уникального бизнес-номера заявки
        request_number = await self._generate_request_number()

        # 6. Сохранение заявки и позиций через репозиторий с DTO
        quote_request_id = await self._save_quote_request(
            data=data,
            request_number=request_number,
            currency=currency,
            vat_rate=vat_rate,
            total_price=totals.total_price,
            rope_items=resolved_rope_items,
            service_items=resolved_service_items,
        )

        loaded = await self.quote_repo.get_by_id(quote_request_id)
        return QuoteRequestResponseDTO.model_validate(loaded)

    def _validate_request_items(self, data: QuoteRequestCreate) -> None:
        """Валидация наличия и состава позиций заявки для выбранного типа конфигуратора."""
        if not data.rope_items and not data.service_items:
            raise QuoteRequestValidationError("Quote request must contain at least one item.")

        if data.configurator_type == ConfiguratorType.ROPE_WITH_SPLICE and not data.rope_items:
            raise QuoteRequestValidationError(
                "Rope with splice configurator requires at least one rope item."
            )

        if data.configurator_type in (ConfiguratorType.LOOP_ONLY, ConfiguratorType.SPLICE_ONLY) and not data.service_items:
            raise QuoteRequestValidationError(
                f"{data.configurator_type.value} configurator requires at least one service item."
            )

    async def _get_configurator_setting(self) -> Tuple[Currency, float, float]:
        """Получение системных параметров конфигуратора (валюта, ставка НДС, тариф за срочность)."""
        stmt_setting = select(ConfiguratorSetting).limit(1)
        setting_res = await self.session.execute(stmt_setting)
        setting = setting_res.scalar_one_or_none()

        currency = setting.currency if setting else Currency.EUR
        vat_rate = float(setting.vat_rate) if setting else 0.0
        urgent_surcharge = float(setting.urgent_surcharge_per_splice) if setting else 10.0

        return currency, vat_rate, urgent_surcharge

    async def _resolve_rope_items(
        self,
        items: List[QuoteRopeItemCreate],
        locale: Language,
    ) -> List[ResolvedRopeItemDTO]:
        """Разрешение списка конфигураций канатов в DTO снимков."""
        resolved: List[ResolvedRopeItemDTO] = []
        for r_item in items:
            resolved_item = await self._resolve_single_rope_item(r_item, locale)
            resolved.append(resolved_item)
        return resolved

    async def _resolve_single_rope_item(
        self,
        r_item: QuoteRopeItemCreate,
        locale: Language,
    ) -> ResolvedRopeItemDTO:
        """Валидация и построение DTO-снимка для отдельной позиции каната."""
        rope_product = await self.rope_product_repo.get_by_id(
            r_item.rope_product_id,
            include_relations=True,
        )
        if not rope_product:
            raise RopeProductNotFoundForQuote(
                f"RopeProduct with product_id {r_item.rope_product_id} not found."
            )

        variant = await self.variant_repo.get_by_product_and_diameter(
            rope_product_id=r_item.rope_product_id,
            diameter_mm=r_item.diameter_mm,
        )
        if not variant:
            raise RopeVariantNotFoundForQuote(
                f"Variant with diameter {r_item.diameter_mm} mm not found for product {r_item.rope_product_id}."
            )

        color = await self.color_repo.get_by_id(r_item.color_id)
        if not color:
            raise ColorNotFoundForQuote(f"Color with id {r_item.color_id} not found.")

        self._validate_product_color_compatibility(rope_product, r_item.color_id)

        product_name_snapshot = self._extract_rope_product_name(rope_product, locale)
        color_name_snapshot = color._get_field_with_translation(
            lambda t: t.name, locale
        ) or color.code

        price_per_meter = float(variant.price_per_meter)
        total_rope_cost = round(price_per_meter * float(r_item.length_m) * r_item.quantity, 2)

        # Разрешение снимков законцовок A и B
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

        return ResolvedRopeItemDTO(
            rope_product_id=r_item.rope_product_id,
            color_id=r_item.color_id,
            product_name_snapshot=product_name_snapshot,
            color_name_snapshot=color_name_snapshot,
            diameter_mm=r_item.diameter_mm,
            length_m=r_item.length_m,
            quantity=r_item.quantity,
            price_per_meter_snapshot=price_per_meter,
            total_rope_cost=total_rope_cost,
            end_a_type_id=r_item.end_a_type_id,
            end_a_name_snapshot=end_a.name_snapshot,
            end_a_eye_size_cm=r_item.end_a_eye_size_cm,
            end_a_cost=end_a.cost,
            end_b_type_id=r_item.end_b_type_id,
            end_b_name_snapshot=end_b.name_snapshot,
            end_b_eye_size_cm=r_item.end_b_eye_size_cm,
            end_b_cost=end_b.cost,
        )

    def _validate_product_color_compatibility(self, rope_product: RopeProduct, color_id: int) -> None:
        """Проверка доступности выбранного цвета для каната."""
        assigned_color_ids = [c.color_id for c in rope_product.colors]
        if assigned_color_ids and color_id not in assigned_color_ids:
            raise ColorNotAllowedForProduct(
                f"Color {color_id} is not available for rope product {rope_product.product_id}."
            )

    def _extract_rope_product_name(self, rope_product: RopeProduct, locale: Language) -> str:
        """Формирование читаемого названия каната для исторического снимка."""
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
        rope_product: RopeProduct,
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

        allowed_ids = [s.splice_type_id for s in rope_product.allowed_splices]
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
                f"No price rule found for splice type {splice_type_id}, "
                f"material {rope_product.splice_material_id}, diameter {diameter_mm} mm."
            )

        name_snapshot = splice_type._get_field_with_translation(
            lambda t: t.name, locale
        ) or splice_type.code
        cost = round(float(unit_price) * quantity, 2)

        return ResolvedEndSpliceDTO(name_snapshot=name_snapshot, cost=cost)

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
                f"No price rule found for service {s_item.splice_type_id}, "
                f"material {s_item.splice_material_id}, diameter {s_item.diameter_mm} mm."
            )

        service_name_snapshot = splice_type._get_field_with_translation(
            lambda t: t.name, locale
        ) or splice_type.code
        material_name_snapshot = splice_material.name
        unit_price_snapshot = float(unit_price)
        total_cost = round(unit_price_snapshot * s_item.quantity, 2)

        return ResolvedServiceItemDTO(
            splice_type_id=s_item.splice_type_id,
            splice_material_id=s_item.splice_material_id,
            service_name_snapshot=service_name_snapshot,
            material_name_snapshot=material_name_snapshot,
            diameter_mm=s_item.diameter_mm,
            eye_size_cm=s_item.eye_size_cm,
            quantity=s_item.quantity,
            unit_price_snapshot=unit_price_snapshot,
            total_cost=total_cost,
        )

    def _calculate_totals(
        self,
        rope_items: List[ResolvedRopeItemDTO],
        service_items: List[ResolvedServiceItemDTO],
        is_urgent: bool,
        urgent_surcharge_per_splice: float,
    ) -> QuoteRequestTotalsDTO:
        """Расчет общей стоимости заявки, включая надбавку за срочность."""
        subtotal = sum(r.total_cost for r in rope_items) + sum(s.total_cost for s in service_items)

        urgent_surcharge = 0.0
        if is_urgent:
            total_splices = sum(r.splices_count for r in rope_items) + sum(s.splices_count for s in service_items)
            urgent_surcharge = total_splices * urgent_surcharge_per_splice

        total_price = round(subtotal + urgent_surcharge, 2)
        return QuoteRequestTotalsDTO(
            subtotal=round(subtotal, 2),
            urgent_surcharge=round(urgent_surcharge, 2),
            total_price=total_price,
        )

    async def _save_quote_request(
        self,
        data: QuoteRequestCreate,
        request_number: str,
        currency: Currency,
        vat_rate: float,
        total_price: float,
        rope_items: List[ResolvedRopeItemDTO],
        service_items: List[ResolvedServiceItemDTO],
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
                rope_product_id=r_dto.rope_product_id,
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

        await self.session.commit()
        return quote_request.id

    async def get_quote_request_by_id(self, request_id: int) -> QuoteRequestResponseDTO:
        """Получение детальной информации о заявке со всеми позициями."""
        item = await self.quote_repo.get_by_id(request_id)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")
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
    ) -> List[QuoteRequestResponseDTO]:
        """Получение списка заявок с гибкой фильтрацией и сортировкой."""
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
        return [QuoteRequestResponseDTO.model_validate(i) for i in items]

    async def update_quote_request(
        self,
        request_id: int,
        data: QuoteRequestUpdateDTO
    ) -> QuoteRequestResponseDTO:
        """Обновление характеристик заявки администратором."""
        item = await self.quote_repo.get_by_id(request_id)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("Did not transmit data")

        if "email" in update_dict and update_dict["email"] is not None:
            update_dict["email"] = str(update_dict["email"])

        await self.quote_repo.update_quote_request(request_id, update_dict)
        await self.session.commit()

        updated = await self.quote_repo.get_by_id(request_id)
        return QuoteRequestResponseDTO.model_validate(updated)

    async def update_quote_request_status(
        self,
        request_id: int,
        status: QuoteRequestStatus
    ) -> QuoteRequestResponseDTO:
        """Изменение статуса заявки администратором."""
        item = await self.quote_repo.get_by_id(request_id)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")

        await self.quote_repo.update_quote_request(request_id, {"status": status})
        await self.session.commit()

        updated = await self.quote_repo.get_by_id(request_id)
        return QuoteRequestResponseDTO.model_validate(updated)

    async def delete_quote_request(self, request_id: int) -> None:
        """Удаление заявки администратором."""
        item = await self.quote_repo.get_by_id(request_id)
        if not item:
            raise QuoteRequestNotFound(f"QuoteRequest with id {request_id} not found.")

        await self.quote_repo.delete_quote_request(request_id)
        await self.session.commit()

    async def _generate_request_number(self) -> str:
        """Генерация уникального читаемого номера заявки формата RPL-YYYY-NNNN."""
        year = datetime.now().year
        count = await self.quote_repo.count_requests_by_year(year)

        candidate = f"RPL-{year}-{count + 1:04d}"
        if not await self.quote_repo.get_by_request_number(candidate, include_relations=False):
            return candidate

        for _ in range(10):
            suffix = "".join(random.choices(string.digits, k=4))
            candidate = f"RPL-{year}-{count + 1:04d}-{suffix}"
            if not await self.quote_repo.get_by_request_number(candidate, include_relations=False):
                return candidate

        rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"RPL-{year}-{rand_suffix}"
