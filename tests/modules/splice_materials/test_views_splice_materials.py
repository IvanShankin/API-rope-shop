import pytest
from sqlalchemy import select

from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
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
