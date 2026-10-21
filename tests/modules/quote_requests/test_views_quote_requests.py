import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from src.modules.configurator_setting.models import Currency
from src.modules.configurator_extra.models import BillingType
from src.modules.quote_requests.models import (
    QuoteRequest,
    ConfiguratorType,
    QuoteRequestStatus,
)
from src.modules.quote_requests.models_dto import (
    QuoteRequestCreate,
    QuoteRopeItemCreate,
    QuoteServiceItemCreate,
    QuoteExtraItemCreate,
    QuoteRequestUpdateStatusDTO,
    QuoteRequestResponseDTO,
    )
from tests.modules.configurator_setting.fixtures.models_dto import CreateConfiguratorSettingFixtureDTO
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.material_groups.fixtures.models_dto import CreateMaterialGroupFixtureDTO
from tests.modules.colors.fixtures.models_dto import CreateColorFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from tests.modules.rope_allowed_splice.fixtures.models_dto import CreateRopeAllowedSpliceFixtureDTO
from tests.modules.quote_requests.fixtures.models_dto import (
    CreateQuoteRequestFixtureDTO,
    CreateQuoteRopeItemFixtureDTO,
    CreateQuoteServiceItemFixtureDTO,
    CreateQuoteExtraItemFixtureDTO,
)
from tests.modules.configurator_extra.fixtures.models_dto import CreateConfiguratorExtraFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_create_quote_request_rope_with_splice_full_calculation(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
        create_material_group_fixture,
        create_splice_material_fixture,
        create_color_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_rope_allowed_splice_fixture,
        create_configurator_extra_fixture,
    ):
        """
        Полный сценарий создания заявки конфигуратора 1: ROPE_WITH_SPLICE.
        Проверяет математику расчета длины с учетом припуска (splice allowance),
        стоимости каната, стоимости заделок концов A и B, доп. опций и НДС.
        """
        # 1. Системные настройки: до 12мм припуск 0.6м на заделку, vat_rate=19%
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(
                min_length_m=1.0,
                max_length_m=200.0,
                splice_allowance_until_mm=12.0,
                splice_allowance_until_m=0.6,
                splice_allowance_over_m=1.0,
                urgent_surcharge_per_splice=10.0,
                urgent_max_splices=10,
                vat_rate=19.0,
            )
        )

        # 2. Справочники
        group = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(name="Racing Group"))
        splice_mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(name="Racing Core"))
        color = await create_color_fixture(CreateColorFixtureDTO(name="Deep Blue"))
        splice_a = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(name="Augspleiss"))
        splice_b = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(name="Takling"))

        # 3. Канат и модификация
        product = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(
                material_group_id=group.id,
                splice_material_id=splice_mat.id,
                can_be_spliced=True,
                construction="12-strand Braided",
            )
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=4.50,
            )
        )
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color.id,
            )
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=product.product_id,
                splice_type_id=splice_a.id,
            )
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                product_id=product.product_id,
                splice_type_id=splice_b.id,
            )
        )

        # 4. Правила цен на заделки
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=splice_a.id,
                splice_material_id=splice_mat.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=20.00,
            )
        )
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=splice_b.id,
                splice_material_id=splice_mat.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=15.00,
            )
        )

        # 5. Доп. опции
        extra_fixed = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="CERT",
                name="Safety Certificate",
                billing_type=BillingType.FIXED,
                price=25.0,
            )
        )
        extra_meter = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="COAT",
                name="UV Coating",
                billing_type=BillingType.PER_METER,
                price=0.50,
            )
        )

        # 6. Запрос на создание заявки
        # Клиент заказывает 10м каната 10мм с заделками A и B (срочный заказ is_urgent=True)
        # Припуск: 2 заделки * 0.6м = 1.2м. Итого оплачиваемая длина каната = 11.2м
        # Стоимость каната: 11.2 * 4.50 = 50.40 EUR
        # Заделка A: 20.00 EUR
        # Заделка B: 15.00 EUR
        # Срочность за 2 заделки: 2 * 10.00 = 20.00 EUR
        # Доп опция FIXED: 25.00 EUR
        # Доп опция PER_METER: 10.00м (чистая длина) * 0.50 = 5.00 EUR
        # Итого = 50.40 + 20.00 + 15.00 + 20.00 + 25.00 + 5.00 = 135.40 EUR
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="John Doe",
            email="john@example.com",
            phone="+4912345678",
            comment="Urgent yacht order",
            is_urgent=True,
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=10.0,
                    length_m=10.0,
                    quantity=1,
                    end_a_type_id=splice_a.id,
                    end_a_eye_size_cm=15.0,
                    end_b_type_id=splice_b.id,
                )
            ],
            extra_items=[
                QuoteExtraItemCreate(extra_id=extra_fixed.id),
                QuoteExtraItemCreate(extra_id=extra_meter.id),
            ],
        )

        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 201

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.request_number.startswith("RPL-")
        assert dto.configurator_type == ConfiguratorType.ROPE_WITH_SPLICE
        assert dto.is_urgent is True
        assert float(dto.vat_rate) == 19.0
        assert float(dto.subtotal) == 115.40
        assert float(dto.urgent_surcharge) == 20.00
        assert float(dto.total_price) == 135.40

        # Проверка снимков позиций
        assert len(dto.rope_items) == 1
        item = dto.rope_items[0]
        assert float(item.price_per_meter_snapshot) == 4.50
        assert float(item.total_rope_cost) == 50.40
        assert float(item.end_a_cost) == 20.00
        assert item.end_a_name_snapshot == "Augspleiss"
        assert float(item.end_b_cost) == 15.00
        assert item.end_b_name_snapshot == "Takling"
        assert item.product_name_snapshot == "12-strand Braided"
        assert item.color_name_snapshot == "Deep Blue"

        # Проверка доп. опций
        assert len(dto.extra_items) == 2
        extra_map = {e.name_snapshot: e for e in dto.extra_items}
        assert float(extra_map["Safety Certificate"].total_cost) == 25.00
        assert float(extra_map["UV Coating"].total_cost) == 5.00

    @pytest.mark.asyncio
    async def test_create_quote_request_persists_custom_locale(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
        create_material_group_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
    ):
        """Проверка сохранения кастомной локали (rus) в БД и возврата в DTO."""
        await create_configurator_setting_fixture(CreateConfiguratorSettingFixtureDTO())
        group = await create_material_group_fixture()
        color = await create_color_fixture()
        product = await create_rope_product_fixture(CreateRopeProductFixtureDTO(material_group_id=group.id))
        await create_rope_variant_fixture(CreateRopeVariantFixtureDTO(product_id=product.product_id, size_value=8.0, price=2.0))
        await create_rope_product_color_fixture(CreateRopeProductColorFixtureDTO(product_id=product.product_id, color_id=color.id))

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Иван Петров",
            email="ivan@example.com",
            phone="+79991234567",
            locale=Language.RUS,
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=8.0,
                    length_m=5.0,
                    quantity=1,
                )
            ],
        )

        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 201
        data = response.json()
        assert data["locale"] == "rus"

        # Check public fetch by number with token
        token = data["tracking_token"]
        req_num = data["request_number"]
        get_res = await client_for_tests.get(f"/quote_requests/number/{req_num}?token={token}")
        assert get_res.status_code == 200
        assert get_res.json()["locale"] == "rus"

    @pytest.mark.asyncio
    async def test_create_quote_request_loop_only(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
        create_material_group_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
        create_configurator_extra_fixture,
    ):
        """
        Сценарий создания заявки конфигуратора 2: LOOP_ONLY (услуга изготовления петель на канат заказчика).
        """
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(
                urgent_surcharge_per_splice=15.0,
                vat_rate=0.0,
            )
        )
        splice_mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(name="Standard Core"))
        splice_loop = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(name="Soft Shackle Loop"))

        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=splice_loop.id,
                splice_material_id=splice_mat.id,
                diameter_from_mm=10.0,
                diameter_to_mm=16.0,
                price=30.00,
            )
        )

        # Стоимость: 2 петли * 30.00 EUR = 60.00 EUR (не срочно)
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.LOOP_ONLY,
            name="Alice",
            email="alice@example.com",
            is_urgent=False,
            service_items=[
                QuoteServiceItemCreate(
                    splice_type_id=splice_loop.id,
                    splice_material_id=splice_mat.id,
                    diameter_mm=12.0,
                    eye_size_cm=20.0,
                    quantity=2,
                )
            ],
        )

        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 201

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.configurator_type == ConfiguratorType.LOOP_ONLY
        assert float(dto.total_price) == 60.00
        assert len(dto.service_items) == 1
        s_item = dto.service_items[0]
        assert s_item.service_name_snapshot == "Soft Shackle Loop"
        assert s_item.material_name_snapshot == "Standard Core"
        assert float(s_item.unit_price_snapshot) == 30.00
        assert float(s_item.total_cost) == 60.00

    @pytest.mark.asyncio
    async def test_get_quote_request_by_number_and_id(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Получение заявки по ID (админ) и публичное получение по номеру заявки request_number."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        quote = await create_quote_request_fixture(
            CreateQuoteRequestFixtureDTO(
                name="Special Order",
                request_number="RPL-2026-9999",
            )
        )

        # 1. Получение по уникальному номеру
        res_by_num = await client_for_tests.get(
            "/quote_requests/number/RPL-2026-9999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res_by_num.status_code == 200
        dto_num = QuoteRequestResponseDTO.model_validate(res_by_num.json())
        assert dto_num.id == quote.id
        assert dto_num.name == "Special Order"

        # 2. Получение админом по числовому ID
        res_by_id = await client_for_tests.get(
            f"/quote_requests/{quote.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res_by_id.status_code == 200
        dto_id = QuoteRequestResponseDTO.model_validate(res_by_id.json())
        assert dto_id.id == quote.id

    @pytest.mark.asyncio
    async def test_list_quote_requests_admin_pagination_filters(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Список заявок с фильтрацией по статусу и пагинацией для администратора."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        q1 = await create_quote_request_fixture(CreateQuoteRequestFixtureDTO(status=QuoteRequestStatus.NEW))
        q2 = await create_quote_request_fixture(CreateQuoteRequestFixtureDTO(status=QuoteRequestStatus.COMPLETED))

        response = await client_for_tests.get(
            "/quote_requests",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"status": "completed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        items = [QuoteRequestResponseDTO.model_validate(i) for i in data["items"]]
        assert any(item.id == q2.id for item in items)
        assert not any(item.id == q1.id for item in items)

    @pytest.mark.asyncio
    async def test_update_quote_request_status(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Администратор изменяет статус заявки."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        quote = await create_quote_request_fixture(CreateQuoteRequestFixtureDTO(status=QuoteRequestStatus.NEW))

        up_body = QuoteRequestUpdateStatusDTO(status=QuoteRequestStatus.CONFIRMED)
        response = await client_for_tests.patch(
            f"/quote_requests/{quote.id}/status",
            headers={"Authorization": f"Bearer {access_token}"},
            json=up_body.model_dump(),
        )
        assert response.status_code == 200
        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.status == QuoteRequestStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_create_quote_request_decimal_precision(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
        create_material_group_fixture,
        create_splice_material_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_configurator_extra_fixture,
    ):
        """Проверка точности финансовых расчетов с использованием Decimal (исключение погрешностей IEEE-754)."""
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(
                min_length_m=0.1,
                max_length_m=200.0,
                splice_allowance_until_mm=12.0,
                splice_allowance_until_m=0.0,
                splice_allowance_over_m=0.0,
                urgent_surcharge_per_splice=0.0,
                vat_rate=0.0,
            )
        )
        group = await create_material_group_fixture()
        splice_mat = await create_splice_material_fixture()
        color = await create_color_fixture()

        product = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(
                material_group_id=group.id,
                splice_material_id=splice_mat.id,
                can_be_spliced=True,
            )
        )
        # Цена 0.10 за метр
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="8 мм",
                size_value=8.0,
                price=0.10,
            )
        )
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color.id,
            )
        )
        # Доп. опция с ценой 0.20
        extra = await create_configurator_extra_fixture(
            CreateConfiguratorExtraFixtureDTO(
                code="EXTRA_PRECISION",
                billing_type=BillingType.FIXED,
                price=0.20,
            )
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Decimal Precision Test",
            email="precision@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=8.0,
                    length_m=1.0,
                    quantity=1,
                )
            ],
            extra_items=[
                QuoteExtraItemCreate(extra_id=extra.id),
            ],
        )

        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 201

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        # В IEEE-754 0.1 + 0.2 = 0.30000000000000004
        # С Decimal subtotal и total_price должны быть строго равны 0.30
        assert dto.subtotal == 0.30
        assert dto.total_price == 0.30


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_create_quote_request_empty_items(
        self,
        client_for_tests,
    ):
        """Попытка создания заявки вообще без позиций -> 400 Bad Request."""
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Empty Client",
            email="empty@example.com",
            rope_items=[],
            service_items=[],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400
        assert "At least one item" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_quote_request_rope_items_in_loop_only_forbidden(
        self,
        client_for_tests,
    ):
        """Передача rope_items в конфигуратор LOOP_ONLY -> 400 Bad Request."""
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.LOOP_ONLY,
            name="Invalid Client",
            email="invalid@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=1,
                    color_id=1,
                    diameter_mm=10.0,
                    length_m=10.0,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400
        assert "rope_items are not allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_quote_request_service_items_in_rope_configurator_forbidden(
        self,
        client_for_tests,
    ):
        """Передача service_items в конфигуратор ROPE_WITH_SPLICE -> 400 Bad Request."""
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Invalid Client",
            email="invalid@example.com",
            service_items=[
                QuoteServiceItemCreate(
                    splice_type_id=1,
                    splice_material_id=1,
                    diameter_mm=10.0,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400
        assert "service_items are not allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_quote_request_length_out_of_bounds(
        self,
        client_for_tests,
        create_material_group_fixture,
        create_splice_material_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_configurator_setting_fixture,
    ):
        """Проверка соблюдения min_length_m и max_length_m из ConfiguratorSetting -> 400."""
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(min_length_m=5.0, max_length_m=100.0)
        )
        product = await create_rope_product_fixture()
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
            )
        )
        color = await create_color_fixture()
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(product_id=product.product_id, color_id=color.id)
        )

        # 1. Меньше min_length_m (2.0 < 5.0)
        req_too_short = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Short Client",
            email="short@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=10.0,
                    length_m=2.0,
                )
            ],
        )
        res1 = await client_for_tests.post("/quote_requests", json=req_too_short.model_dump())
        assert res1.status_code == 400
        assert "less than minimum allowed" in res1.json()["detail"]

        # 2. Больше max_length_m (150.0 > 100.0)
        req_too_long = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Long Client",
            email="long@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=10.0,
                    length_m=150.0,
                )
            ],
        )
        res2 = await client_for_tests.post("/quote_requests", json=req_too_long.model_dump())
        assert res2.status_code == 400
        assert "exceeds maximum allowed" in res2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_quote_request_urgent_exceeds_max_splices(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Срочный заказ превышает лимит urgent_max_splices заделок -> 400 Bad Request."""
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(urgent_max_splices=2)
        )
        splice_mat = await create_splice_material_fixture()
        splice_loop = await create_splice_type_fixture()
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=splice_loop.id,
                splice_material_id=splice_mat.id,
                diameter_from_mm=8.0,
                diameter_to_mm=14.0,
                price=10.0,
            )
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.LOOP_ONLY,
            name="Overloaded Client",
            email="overload@example.com",
            is_urgent=True,
            service_items=[
                QuoteServiceItemCreate(
                    splice_type_id=splice_loop.id,
                    splice_material_id=splice_mat.id,
                    diameter_mm=10.0,
                    quantity=3,  # 3 splices > limit 2
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400
        assert "Urgent processing exceeds maximum allowed splices" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_quote_request_product_not_found(
        self,
        client_for_tests,
        create_color_fixture,
    ):
        """Несуществующий товар-канат -> 404."""
        color = await create_color_fixture()
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=999999,
                    color_id=color.id,
                    diameter_mm=10.0,
                    length_m=10.0,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_quote_request_variant_not_found(
        self,
        client_for_tests,
        create_color_fixture,
        create_rope_product_fixture,
    ):
        """Несуществующий диаметр для каната -> 404."""
        color = await create_color_fixture()
        product = await create_rope_product_fixture()

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=99.0,  # Variant does not exist
                    length_m=10.0,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_quote_request_color_not_allowed(
        self,
        client_for_tests,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
    ):
        """Цвет существует, но не привязан к данному товару -> 400 Bad Request."""
        product = await create_rope_product_fixture()
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
            )
        )
        allowed_color = await create_color_fixture(CreateColorFixtureDTO(code="allowed_col"))
        disallowed_color = await create_color_fixture(CreateColorFixtureDTO(code="disallowed_col"))

        # Привязываем только allowed_color
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(product_id=product.product_id, color_id=allowed_color.id)
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=disallowed_color.id,  # not linked
                    diameter_mm=10.0,
                    length_m=10.0,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_quote_request_splice_price_rule_not_found(
        self,
        client_for_tests,
        create_splice_type_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Для выбранного сращивания и диаметра нет ценового правила в прайс-листе -> 400 Bad Request."""
        splice_type = await create_splice_type_fixture()
        color = await create_color_fixture()
        product = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(can_be_spliced=True)
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(
                product_id=product.product_id,
                variant_name="10 мм",
                size_value=10.0,
                price=5.0,
            )
        )
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(product_id=product.product_id, color_id=color.id)
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(product_id=product.product_id, splice_type_id=splice_type.id)
        )
        # We do NOT create any SplicePriceRule!

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=10.0,
                    length_m=10.0,
                    end_a_type_id=splice_type.id,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400
        assert "No pricing rule found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_quote_requests_unauthorized(
        self,
        client_for_tests,
    ):
        """Список всех заявок без авторизации -> 401."""
        response = await client_for_tests.get("/quote_requests")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_quote_requests_forbidden_for_user(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Список всех заявок обычным пользователем -> 403."""
        user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))
        response = await client_for_tests.get(
            "/quote_requests",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_quote_request_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Запрос несуществующей заявки по ID -> 404."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        response = await client_for_tests.get(
            "/quote_requests/999999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_quote_request_by_number_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Запрос несуществующего номера заявки -> 404."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        response = await client_for_tests.get(
            "/quote_requests/number/NON-EXISTENT-NUM",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404
