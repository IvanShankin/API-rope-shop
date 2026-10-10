import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.material_groups.fixtures.models_dto import CreateMaterialGroupFixtureDTO
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from tests.modules.colors.fixtures.models_dto import CreateColorFixtureDTO
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
)
from src.modules.splice_types.models import SpliceCategory
from src.modules.quote_requests.models import (
    QuoteRequest,
    QuoteRopeItem,
    ConfiguratorType,
    QuoteRequestStatus,
)
from src.modules.quote_requests.models_dto import (
    QuoteRequestCreate,
    QuoteRopeItemCreate,
    QuoteServiceItemCreate,
    QuoteRequestUpdateDTO,
    QuoteRequestUpdateStatusDTO,
    QuoteRequestResponseDTO,
)


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_create_quote_request_rope_with_splice(
        self,
        client_for_tests,
        create_material_group_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Создание заявки конфигуратора 1 (канат + петли) с расчетом снимков цен и названий."""
        group = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(name="Standard Group"))
        splice_mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(name="Kern-Mantel Mat"))
        splice_type = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(category=SpliceCategory.LOOP, name="Augspleiss")
        )

        color = await create_color_fixture(CreateColorFixtureDTO(code="red_color", name="Red Color"))

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
                rope_product_id=product.product_id,
                diameter_mm=10.0,
                price_per_meter=4.50,
            )
        )
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                rope_product_id=product.product_id,
                color_id=color.id,
            )
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(
                rope_product_id=product.product_id,
                splice_type_id=splice_type.id,
            )
        )
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_material_id=splice_mat.id,
                splice_type_id=splice_type.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=15.00,
            )
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Ivan Customer",
            email="ivan@example.com",
            phone="+4912345678",
            comment="Urgent yacht project",
            is_urgent=False,
            locale=Language.ENG,
            rope_items=[
                QuoteRopeItemCreate(
                    rope_product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=10.0,
                    length_m=20.0,
                    quantity=1,
                    end_a_type_id=splice_type.id,
                    end_a_eye_size_cm=15.0,
                )
            ],
        )

        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 201

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.request_number.startswith("RPL-")
        assert dto.status == QuoteRequestStatus.NEW
        assert dto.name == "Ivan Customer"
        assert dto.email == "ivan@example.com"
        assert len(dto.rope_items) == 1

        r_item = dto.rope_items[0]
        assert r_item.rope_product_id == product.product_id
        assert r_item.product_name_snapshot == "12-strand Braided"
        assert r_item.color_name_snapshot == "Red Color"
        assert r_item.diameter_mm == 10.0
        assert r_item.price_per_meter_snapshot == 4.50
        assert r_item.total_rope_cost == 90.00  # 20m * 4.50
        assert r_item.end_a_cost == 15.00
        assert r_item.end_a_name_snapshot == "Augspleiss"
        assert r_item.end_b_cost == 0.00
        assert dto.total_price == 105.00  # 90 + 15

    @pytest.mark.asyncio
    async def test_create_quote_request_service_only(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Создание заявки конфигуратора 2/3 (только петли / сращивание)."""
        splice_mat = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(name="Dyneema Mat"))
        splice_type = await create_splice_type_fixture(
            CreateSpliceTypeFixtureDTO(category=SpliceCategory.LOOP, name="Endless Spleiss")
        )
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_material_id=splice_mat.id,
                splice_type_id=splice_type.id,
                diameter_from_mm=10.0,
                diameter_to_mm=14.0,
                price=25.00,
            )
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.LOOP_ONLY,
            name="John Sailor",
            email="john@example.com",
            phone="+4998765432",
            is_urgent=False,
            locale=Language.ENG,
            service_items=[
                QuoteServiceItemCreate(
                    splice_type_id=splice_type.id,
                    splice_material_id=splice_mat.id,
                    diameter_mm=12.0,
                    eye_size_cm=10.0,
                    quantity=2,
                )
            ],
        )

        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 201

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert len(dto.service_items) == 1
        s_item = dto.service_items[0]
        assert s_item.splice_type_id == splice_type.id
        assert s_item.service_name_snapshot == "Endless Spleiss"
        assert s_item.material_name_snapshot == "Dyneema Mat"
        assert s_item.unit_price_snapshot == 25.00
        assert s_item.total_cost == 50.00  # 2 * 25.00
        assert dto.total_price == 50.00

    @pytest.mark.asyncio
    async def test_create_quote_request_urgent_surcharge(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Расчет надбавки за срочность (is_urgent=True)."""
        splice_mat = await create_splice_material_fixture()
        splice_type = await create_splice_type_fixture()
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_material_id=splice_mat.id,
                splice_type_id=splice_type.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=20.00,
            )
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.LOOP_ONLY,
            name="Urgent Client",
            email="urgent@example.com",
            is_urgent=True,
            service_items=[
                QuoteServiceItemCreate(
                    splice_type_id=splice_type.id,
                    splice_material_id=splice_mat.id,
                    diameter_mm=10.0,
                    quantity=2,
                )
            ],
        )

        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 201

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.is_urgent is True
        # subtotal: 2 * 20 = 40.0, urgent: 2 * 10 = 20.0, total: 60.0
        assert dto.total_price == 60.00

    @pytest.mark.asyncio
    async def test_list_quote_requests_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Получение списка заявок администратором."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        q1 = await create_quote_request_fixture(CreateQuoteRequestFixtureDTO(name="Alice"))
        q2 = await create_quote_request_fixture(CreateQuoteRequestFixtureDTO(name="Bob"))

        response = await client_for_tests.get(
            "/quote_requests",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = [QuoteRequestResponseDTO.model_validate(item) for item in response.json()]
        ids = [item.id for item in data]
        assert q1.id in ids
        assert q2.id in ids

    @pytest.mark.asyncio
    async def test_list_quote_requests_filters_and_search(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Фильтрация по статусу, configurator_type, email и текстовому поиску search."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        q_target = await create_quote_request_fixture(
            CreateQuoteRequestFixtureDTO(
                name="Special VIP",
                email="vip_special@ocean.com",
                status=QuoteRequestStatus.CONFIRMED,
                configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            )
        )
        q_other = await create_quote_request_fixture(
            CreateQuoteRequestFixtureDTO(
                name="Normal Guy",
                email="normal@sea.com",
                status=QuoteRequestStatus.NEW,
                configurator_type=ConfiguratorType.LOOP_ONLY,
            )
        )

        # 1. Filter by status
        resp = await client_for_tests.get(
            "/quote_requests",
            params={"status": "confirmed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()
        assert any(i["id"] == q_target.id for i in items)
        assert not any(i["id"] == q_other.id for i in items)

        # 2. Search query
        resp_search = await client_for_tests.get(
            "/quote_requests",
            params={"search": "vip_special"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_search.status_code == 200
        items_search = resp_search.json()
        assert len(items_search) == 1
        assert items_search[0]["id"] == q_target.id

    @pytest.mark.asyncio
    async def test_get_quote_request_detail_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Получение детальной информации о заявке администратором."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        q = await create_quote_request_fixture(
            CreateQuoteRequestFixtureDTO(
                rope_items=[CreateQuoteRopeItemFixtureDTO(product_name_snapshot="Racer Rope")]
            )
        )

        response = await client_for_tests.get(
            f"/quote_requests/{q.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.id == q.id
        assert len(dto.rope_items) == 1
        assert dto.rope_items[0].product_name_snapshot == "Racer Rope"

    @pytest.mark.asyncio
    async def test_update_quote_request_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Обновление характеристик заявки администратором."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        q = await create_quote_request_fixture(CreateQuoteRequestFixtureDTO(comment="Old comment"))

        update_dto = QuoteRequestUpdateDTO(comment="Updated admin comment", total_price=150.0)
        response = await client_for_tests.patch(
            f"/quote_requests/{q.id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_dto.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.comment == "Updated admin comment"
        assert dto.total_price == 150.0

    @pytest.mark.asyncio
    async def test_update_quote_request_status_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Изменение статуса заявки администратором."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        q = await create_quote_request_fixture(CreateQuoteRequestFixtureDTO(status=QuoteRequestStatus.NEW))

        response = await client_for_tests.patch(
            f"/quote_requests/{q.id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json=QuoteRequestUpdateStatusDTO(status=QuoteRequestStatus.IN_PROGRESS).model_dump(),
        )
        assert response.status_code == 200

        dto = QuoteRequestResponseDTO.model_validate(response.json())
        assert dto.status == QuoteRequestStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_delete_quote_request_admin(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_quote_request_fixture,
    ):
        """Удаление заявки и каскадное удаление ее позиций."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        q = await create_quote_request_fixture(
            CreateQuoteRequestFixtureDTO(
                rope_items=[CreateQuoteRopeItemFixtureDTO()],
                service_items=[CreateQuoteServiceItemFixtureDTO()],
            )
        )

        response = await client_for_tests.delete(
            f"/quote_requests/{q.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(QuoteRequest).where(QuoteRequest.id == q.id))
        assert res.scalar_one_or_none() is None

        # Проверка удаления дочерних элементов
        res_r = await session_db.execute(select(QuoteRopeItem).where(QuoteRopeItem.quote_request_id == q.id))
        assert res_r.scalars().all() == []


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_create_quote_request_empty_items(
        self,
        client_for_tests,
    ):
        """Попытка создания заявки без позиций -> 400 Bad Request."""
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Empty Client",
            email="empty@example.com",
            rope_items=[],
            service_items=[],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_quote_request_missing_required_configurator_items(
        self,
        client_for_tests,
    ):
        """Попытка создания rope_with_splice только с service_items -> 400 Bad Request."""
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Client",
            email="client@example.com",
            rope_items=[],
            service_items=[
                QuoteServiceItemCreate(
                    splice_type_id=1,
                    splice_material_id=1,
                    diameter_mm=10.0,
                    quantity=1,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_quote_request_rope_product_not_found(
        self,
        client_for_tests,
    ):
        """Несуществующий rope_product_id -> 404."""
        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    rope_product_id=999999,
                    color_id=1,
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
        create_material_group_fixture,
        create_splice_material_fixture,
        create_color_fixture,
        create_rope_product_fixture,
    ):
        """Несуществующий диаметр для каната -> 404."""
        group = await create_material_group_fixture()
        splice_mat = await create_splice_material_fixture()
        color = await create_color_fixture()
        product = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(material_group_id=group.id, splice_material_id=splice_mat.id)
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    rope_product_id=product.product_id,
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
        create_material_group_fixture,
        create_splice_material_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
    ):
        """Цвет существует, но не привязан к данному товару -> 400 Bad Request."""
        group = await create_material_group_fixture()
        splice_mat = await create_splice_material_fixture()
        product = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(material_group_id=group.id, splice_material_id=splice_mat.id)
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(rope_product_id=product.product_id, diameter_mm=10.0)
        )
        allowed_color = await create_color_fixture(CreateColorFixtureDTO(code="allowed_col"))
        disallowed_color = await create_color_fixture(CreateColorFixtureDTO(code="disallowed_col"))

        # Привязываем только allowed_color
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(rope_product_id=product.product_id, color_id=allowed_color.id)
        )

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    rope_product_id=product.product_id,
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
        create_material_group_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_variant_fixture,
        create_rope_product_color_fixture,
        create_rope_allowed_splice_fixture,
    ):
        """Для выбранного сращивания и диаметра нет ценового правила в прайс-листе -> 400 Bad Request."""
        group = await create_material_group_fixture()
        splice_mat = await create_splice_material_fixture()
        splice_type = await create_splice_type_fixture()
        color = await create_color_fixture()
        product = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(
                material_group_id=group.id,
                splice_material_id=splice_mat.id,
                can_be_spliced=True,
            )
        )
        await create_rope_variant_fixture(
            CreateRopeVariantFixtureDTO(rope_product_id=product.product_id, diameter_mm=10.0)
        )
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(rope_product_id=product.product_id, color_id=color.id)
        )
        await create_rope_allowed_splice_fixture(
            CreateRopeAllowedSpliceFixtureDTO(rope_product_id=product.product_id, splice_type_id=splice_type.id)
        )
        # We do NOT create any SplicePriceRule!

        req_body = QuoteRequestCreate(
            configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
            name="Test Client",
            email="test@example.com",
            rope_items=[
                QuoteRopeItemCreate(
                    rope_product_id=product.product_id,
                    color_id=color.id,
                    diameter_mm=10.0,
                    length_m=10.0,
                    end_a_type_id=splice_type.id,
                )
            ],
        )
        response = await client_for_tests.post("/quote_requests", json=req_body.model_dump())
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_quote_requests_unauthorized(
        self,
        client_for_tests,
    ):
        """Попытка просмотра заявок без токена -> 401."""
        response = await client_for_tests.get("/quote_requests")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_quote_requests_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка просмотра обычным пользователем -> 403."""
        user, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))
        response = await client_for_tests.get(
            "/quote_requests",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_quote_request_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Запрос несуществующей заявки -> 404."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        response = await client_for_tests.get(
            "/quote_requests/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
