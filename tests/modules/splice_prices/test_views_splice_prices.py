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

        data = response.json()
        assert len(data) >= 2

        ids = [r['id'] for r in data]
        assert rule_1.id in ids
        assert rule_2.id in ids

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

        result_db = await session_db.execute(select(SplicePriceRule).where(SplicePriceRule.id == updated_rule.id))
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
    async def test_get_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/splice_prices/99999")
        assert response.status_code == 404
