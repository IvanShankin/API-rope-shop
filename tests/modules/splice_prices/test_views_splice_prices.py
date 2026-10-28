import pytest
from sqlalchemy import select

from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from src.modules.splice_prices.models import SplicePriceRule
from src.modules.splice_prices.models_dto import (
    SplicePriceRuleResponseDTO,
    SplicePriceRuleCreate,
    SplicePriceRuleUpdate
)
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from src.modules.splice_prices.repository import SplicePriceRuleRepository
from tests.helpers.functions import comparison_models

class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_rules(
        self,
        client_for_tests,
        create_splice_price_rule_fixture,
    ):
        rule_1 = await create_splice_price_rule_fixture(CreateSplicePriceRuleFixtureDTO())
        rule_2 = await create_splice_price_rule_fixture(CreateSplicePriceRuleFixtureDTO())

        response = await client_for_tests.get("/splice_prices")
        assert response.status_code == 200

        data = [SplicePriceRuleResponseDTO.model_validate(r) for r in response.json()]
        assert len(data) >= 2

        ids = [r.id for r in data]
        assert rule_1.id in ids
        assert rule_2.id in ids

    @pytest.mark.asyncio
    async def test_get_all_rules_filter_is_active(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_price_rule_fixture,
    ):
        """Админ может запросить неактивные правила, а аноним всегда получает только активные."""
        _, admin_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        r_active = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(is_active=True)
        )
        r_inactive = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(is_active=False)
        )

        res_admin = await client_for_tests.get(
            "/splice_prices?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_admin.status_code == 200
        admin_ids = [item["id"] for item in res_admin.json()]
        assert r_inactive.id in admin_ids
        assert r_active.id not in admin_ids

        res_anon = await client_for_tests.get("/splice_prices?is_active=false")
        assert res_anon.status_code == 200
        anon_ids = [item["id"] for item in res_anon.json()]
        assert r_inactive.id not in anon_ids
        assert r_active.id in anon_ids

    @pytest.mark.asyncio
    async def test_get_rule(
        self,
        client_for_tests,
        create_splice_price_rule_fixture,
    ):
        rule = await create_splice_price_rule_fixture(CreateSplicePriceRuleFixtureDTO())

        response = await client_for_tests.get(f"/splice_prices/{rule.id}")
        assert response.status_code == 200

        data = SplicePriceRuleResponseDTO.model_validate(response.json())
        assert comparison_models(rule, data)

    @pytest.mark.asyncio
    async def test_create_rule(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_type_fixture,
        create_splice_material_fixture,
    ):
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        create_data = SplicePriceRuleCreate(
            splice_type_id=st.id,
            splice_material_id=sm.id,
            diameter_from_mm=10.0,
            diameter_to_mm=20.0,
            price=150.75,
            is_active=True
        )

        response = await client_for_tests.post(
            "/splice_prices",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump()
        )
        assert response.status_code == 201

        new_rule = SplicePriceRuleResponseDTO.model_validate(response.json())
        assert new_rule.price == 150.75
        assert new_rule.splice_type_id == st.id
        
        result_db = await session_db.execute(select(SplicePriceRule).where(SplicePriceRule.id == new_rule.id))
        rule_from_db = result_db.scalar_one_or_none()
        assert rule_from_db
        assert comparison_models(new_rule, rule_from_db)

    @pytest.mark.asyncio
    async def test_update_rule(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_price_rule_fixture,
    ):
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        rule = await create_splice_price_rule_fixture(CreateSplicePriceRuleFixtureDTO())

        update_data = SplicePriceRuleUpdate(price=999.99)

        response = await client_for_tests.patch(
            f"/splice_prices/{rule.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True)
        )
        assert response.status_code == 200

        updated_rule = SplicePriceRuleResponseDTO.model_validate(response.json())
        assert updated_rule.price == 999.99

        result_db = await session_db.execute(select(SplicePriceRule).where(SplicePriceRule.id == updated_rule.id))\
            
        rule_from_db = result_db.scalar_one_or_none()
        assert rule_from_db
        assert comparison_models(updated_rule, rule_from_db)

    @pytest.mark.asyncio
    async def test_delete_rule(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_price_rule_fixture,
    ):
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        rule = await create_splice_price_rule_fixture(CreateSplicePriceRuleFixtureDTO())

        response = await client_for_tests.delete(
            f"/splice_prices/{rule.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 204

        result_db = await session_db.execute(select(SplicePriceRule).where(SplicePriceRule.id == rule.id))
        assert not result_db.scalar_one_or_none()

class TestsForErrors:

    @pytest.mark.asyncio
    async def test_create_rule_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        user, access_token = await create_user_fixture(CreateUserFixtureDTO())
        
        create_data = SplicePriceRuleCreate(
            splice_type_id=1,
            splice_material_id=1,
            price=150.75,
        )

        response = await client_for_tests.post(
            "/splice_prices",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_inactive_rule_anonymous_returns_404(
        self,
        client_for_tests,
        create_splice_price_rule_fixture,
    ):
        """Анонимный запрос неактивного правила цен -> 404."""
        rule = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(is_active=False)
        )
        response = await client_for_tests.get(f"/splice_prices/{rule.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/splice_prices/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_price_deterministic_with_multiple_rules(
        self,
        session_db,
        create_splice_type_fixture,
        create_splice_material_fixture,
        create_splice_price_rule_fixture,
    ):
        """Проверка отсутствия MultipleResultsFound при нескольких подходящих правилах."""
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        # Широкое правило (5-20 мм)
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st.id,
                splice_material_id=sm.id,
                diameter_from_mm=5.0,
                diameter_to_mm=20.0,
                price=50.0,
            )
        )
        # Узкое специальное правило (10-18 мм)
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st.id,
                splice_material_id=sm.id,
                diameter_from_mm=10.0,
                diameter_to_mm=18.0,
                price=120.0,
            )
        )

        repo = SplicePriceRuleRepository(session_db)
        # Для диаметра 15мм подходят оба правила: выбирается специальное (120.0) без сбоя MultipleResultsFound
        price_15 = await repo.get_price(material_id=sm.id, type_id=st.id, diameter=15.0)
        assert price_15 == 120.0

        # Для диаметра 8мм подходит только широкое правило (50.0)
        price_8 = await repo.get_price(material_id=sm.id, type_id=st.id, diameter=8.0)
        assert price_8 == 50.0


    @pytest.mark.asyncio
    async def test_applicable_rules_excludes_inactive_splice_type(
        self,
        client_for_tests,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """GET /splice_prices/applicable исключает правила для отключённых типов заделок."""
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="sm_app_test"))
        st_act = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(code="st_app_act", is_active=True))
        st_inact = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(code="st_app_inact", is_active=False))

        r_act = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_act.id,
                splice_material_id=sm.id,
                diameter_from_mm=5.0,
                diameter_to_mm=15.0,
                price=30.0,
                is_active=True,
            )
        )
        r_inact = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_inact.id,
                splice_material_id=sm.id,
                diameter_from_mm=5.0,
                diameter_to_mm=15.0,
                price=50.0,
                is_active=True,
            )
        )

        resp = await client_for_tests.get(
            "/splice_prices/applicable",
            params={"material_id": sm.id, "diameter": 10.0},
        )
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()]
        assert r_act.id in ids
        assert r_inact.id not in ids

    @pytest.mark.asyncio
    async def test_get_rule_with_inactive_splice_type_anonymous_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Аноним получает 404 при запросе правила с отключённым типом заделки, админ получает 200."""
        _, admin_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
        st_inact = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(is_active=False))

        rule = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_type_id=st_inact.id,
                splice_material_id=sm.id,
                is_active=True,
            )
        )

        # Аноним
        resp_anon = await client_for_tests.get(f"/splice_prices/{rule.id}")
        assert resp_anon.status_code == 404

        # Админ
        resp_admin = await client_for_tests.get(
            f"/splice_prices/{rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_admin.status_code == 200
        assert resp_admin.json()["id"] == rule.id

    @pytest.mark.asyncio
    async def test_batch_save_rules_atomic_success(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Проверка успешного атомарного сохранения тарифной сетки (create, update, delete)."""
        _, admin_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        headers = {"Authorization": f"Bearer {admin_token}"}
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())

        # Исходные правила
        rule_to_update = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(splice_material_id=sm.id, splice_type_id=st.id, price=10.0)
        )
        rule_to_delete = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(splice_material_id=sm.id, splice_type_id=st.id, price=15.0)
        )

        batch_payload = {
            "rules": [
                {
                    "id": rule_to_update.id,
                    "splice_material_id": sm.id,
                    "splice_type_id": st.id,
                    "diameter_from_mm": 8.0,
                    "diameter_to_mm": 12.0,
                    "price": 35.0,
                    "is_active": True,
                },
                {
                    "id": None,
                    "splice_material_id": sm.id,
                    "splice_type_id": st.id,
                    "diameter_from_mm": 14.0,
                    "diameter_to_mm": 18.0,
                    "price": 45.0,
                    "is_active": True,
                },
            ],
            "delete_rule_ids": [rule_to_delete.id],
        }

        resp = await client_for_tests.post("/splice_prices/batch", json=batch_payload, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created_count"] == 1
        assert data["updated_count"] == 1
        assert data["deleted_count"] == 1

        # Проверяем обновленное правило
        resp_updated = await client_for_tests.get(f"/splice_prices/{rule_to_update.id}", headers=headers)
        assert resp_updated.status_code == 200
        assert resp_updated.json()["price"] == 35.0

        # Проверяем удаленное правило
        resp_deleted = await client_for_tests.get(f"/splice_prices/{rule_to_delete.id}", headers=headers)
        assert resp_deleted.status_code == 404

    @pytest.mark.asyncio
    async def test_batch_save_rules_atomic_rollback_on_failure(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """При ошибке в любом элементе сетки транзакция полностью откатывается (ни одно изменение не применяется)."""
        _, admin_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        headers = {"Authorization": f"Bearer {admin_token}"}
        sm = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())

        rule = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(splice_material_id=sm.id, splice_type_id=st.id, price=10.0)
        )

        # Пакет содержит валидное обновление первого правила и некорректный диапазон диаметров (from > to)
        batch_payload = {
            "rules": [
                {
                    "id": rule.id,
                    "splice_material_id": sm.id,
                    "splice_type_id": st.id,
                    "price": 999.0,
                },
                {
                    "id": None,
                    "splice_material_id": sm.id,
                    "splice_type_id": st.id,
                    "diameter_from_mm": 20.0,
                    "diameter_to_mm": 10.0,  # Ошибка: from > to
                    "price": 50.0,
                },
            ],
            "delete_rule_ids": [],
        }

        resp = await client_for_tests.post("/splice_prices/batch", json=batch_payload, headers=headers)
        assert resp.status_code == 400

        # Проверяем, что исходное правило НЕ изменилось (цена осталась 10.0, а не 999.0)
        resp_check = await client_for_tests.get(f"/splice_prices/{rule.id}", headers=headers)
        assert resp_check.status_code == 200
        assert resp_check.json()["price"] == 10.0
