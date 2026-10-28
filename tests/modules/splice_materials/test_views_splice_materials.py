import pytest
from sqlalchemy import select

from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from tests.modules.rope_products.fixtures.models_dto import CreateRopeProductFixtureDTO
from tests.modules.material_groups.fixtures.models_dto import CreateMaterialGroupFixtureDTO
from src.modules.splice_materials.models import SpliceMaterial
from src.modules.splice_materials.models_dto import (
    SpliceMaterialResponseDTO, 
    SpliceMaterialCreate,
    SpliceMaterialUpdate
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_splice_materials(
        self,
        client_for_tests,
        create_splice_material_fixture,
    ):
        material_1 = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
        material_2 = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        response = await client_for_tests.get("/splice_materials")

        assert response.status_code == 200

        data = [SpliceMaterialResponseDTO.model_validate(m) for m in response.json()]
        assert len(data) >= 2

        ids = [m.id for m in data]
        assert material_1.id in ids
        assert material_2.id in ids


    @pytest.mark.asyncio
    async def test_get_splice_material(
        self,
        client_for_tests,
        create_splice_material_fixture,
    ):
        material = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        response = await client_for_tests.get(f"/splice_materials/{material.id}")

        assert response.status_code == 200

        data = SpliceMaterialResponseDTO.model_validate(response.json())
        assert comparison_models(material, data)


    @pytest.mark.asyncio
    async def test_create_splice_material(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = SpliceMaterialCreate(
            code="test_code",
            name="test_name",
        )

        response = await client_for_tests.post(
            "/splice_materials",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(),
        )

        assert response.status_code == 201

        new_material = SpliceMaterialResponseDTO.model_validate(response.json())
        assert new_material.code == "test_code"
        assert new_material.name == "test_name"

        result_db = await session_db.execute(select(SpliceMaterial).where(SpliceMaterial.id == new_material.id))
        material_from_db = result_db.scalar_one_or_none()
        
        assert material_from_db
        assert comparison_models(new_material, material_from_db, keys_not_checked=["rules"])


    @pytest.mark.asyncio
    async def test_update_splice_material(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        material = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        update_data = SpliceMaterialUpdate(
            code="new_code",
            name="new_name",
        )

        response = await client_for_tests.patch(
            f"/splice_materials/{material.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )

        assert response.status_code == 200

        updated_material = SpliceMaterialResponseDTO.model_validate(response.json())
        assert updated_material.code == "new_code"
        assert updated_material.name == "new_name"

        result_db = await session_db.execute(select(SpliceMaterial).where(SpliceMaterial.id == updated_material.id))
        material_from_db = result_db.scalar_one_or_none()
        
        assert material_from_db
        assert comparison_models(updated_material, material_from_db, keys_not_checked=["rules"])


    @pytest.mark.asyncio
    async def test_delete_splice_material(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        material = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())

        response = await client_for_tests.delete(
            f"/splice_materials/{material.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 204

        result_db = await session_db.execute(select(SpliceMaterial).where(SpliceMaterial.id == material.id))
        material_from_db = result_db.scalar_one_or_none()
        
        assert not material_from_db


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_create_splice_material_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        user, access_token = await create_user_fixture(CreateUserFixtureDTO())

        create_data = SpliceMaterialCreate(
            code="test_code",
            name="test_name",
        )

        response = await client_for_tests.post(
            "/splice_materials",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(),
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/splice_materials/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_splice_material_has_dependencies(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
    ):
        """Попытка удаления материала сращивания при наличии связанных правил цен -> 400."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        material = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO())
        splice_type = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO())
        await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_material_id=material.id,
                splice_type_id=splice_type.id,
            )
        )

        response = await client_for_tests.delete(
            f"/splice_materials/{material.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "referenced by SplicePriceRules or RopeProducts" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_splice_material_dependencies(
        self,
        client_for_tests,
        create_user_fixture,
        create_splice_material_fixture,
        create_splice_type_fixture,
        create_splice_price_rule_fixture,
        create_material_group_fixture,
        create_rope_product_fixture,
    ):
        """Проверка получения списка зависимостей тарифного материала перед удалением."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. Материал без зависимостей -> has_dependencies=False, can_delete=True
        mat_free = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="free_mat"))
        resp_free = await client_for_tests.get(f"/splice_materials/{mat_free.id}/dependencies", headers=headers)
        assert resp_free.status_code == 200
        data_free = resp_free.json()
        assert data_free["has_dependencies"] is False
        assert data_free["can_delete"] is True
        assert data_free["rules_count"] == 0
        assert data_free["ropes_count"] == 0
        assert data_free["rules"] == []
        assert data_free["ropes"] == []

        # 2. Материал со связями (правило цен + канат с этим тарифным материалом)
        mat_linked = await create_splice_material_fixture(CreateSpliceMaterialFixtureDTO(code="linked_mat"))
        st = await create_splice_type_fixture(CreateSpliceTypeFixtureDTO(code="st_for_mat"))
        rule = await create_splice_price_rule_fixture(
            CreateSplicePriceRuleFixtureDTO(
                splice_material_id=mat_linked.id,
                splice_type_id=st.id,
                diameter_from_mm=8.0,
                diameter_to_mm=12.0,
                price=15.0,
            )
        )
        group = await create_material_group_fixture(CreateMaterialGroupFixtureDTO())
        rope_prod = await create_rope_product_fixture(
            CreateRopeProductFixtureDTO(material_group_id=group.id, splice_material_id=mat_linked.id)
        )

        resp_linked = await client_for_tests.get(f"/splice_materials/{mat_linked.id}/dependencies", headers=headers)
        assert resp_linked.status_code == 200
        data_linked = resp_linked.json()
        assert data_linked["has_dependencies"] is True
        assert data_linked["can_delete"] is False
        assert data_linked["rules_count"] == 1
        assert data_linked["ropes_count"] == 1
        assert len(data_linked["rules"]) == 1
        assert data_linked["rules"][0]["id"] == rule.id
        assert data_linked["rules"][0]["splice_type_code"] == "st_for_mat"
        assert len(data_linked["ropes"]) == 1
        assert data_linked["ropes"][0]["product_id"] == rope_prod.product_id

        # 3. 404 если материал не найден
        resp_404 = await client_for_tests.get("/splice_materials/99999/dependencies", headers=headers)
        assert resp_404.status_code == 404

        # 4. 401 без авторизации
        resp_unauth = await client_for_tests.get(f"/splice_materials/{mat_linked.id}/dependencies")
        assert resp_unauth.status_code == 401
