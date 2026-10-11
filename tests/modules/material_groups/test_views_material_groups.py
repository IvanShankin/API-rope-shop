import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.material_groups.fixtures.models_dto import (
    CreateMaterialGroupFixtureDTO,
    CreateMaterialGroupTranslationFixtureDTO,
)
from tests.modules.rope_products.fixtures.models_dto import CreateRopeProductFixtureDTO
from src.modules.material_groups.models import MaterialGroup, MaterialGroupTranslation
from src.modules.material_groups.models_dto import (
    MaterialGroupCreate,
    MaterialGroupUpdate,
    MaterialGroupUpdateIndexDTO,
    MaterialGroupResponseDTO,
    MaterialGroupLocalizedResponseDTO,
    MaterialGroupTranslationCreate,
    MaterialGroupTranslationUpdate,
    MaterialGroupTranslationResponseDTO,
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_material_groups(
        self,
        client_for_tests,
        create_material_group_fixture,
    ):
        """Получение списка групп материалов с локализацией по умолчанию (ENG)."""
        g1 = await create_material_group_fixture(
            CreateMaterialGroupFixtureDTO(code="standard", name="Standard Ropes", index=1)
        )
        g2 = await create_material_group_fixture(
            CreateMaterialGroupFixtureDTO(code="technical", name="Technical Fibers", index=2)
        )

        response = await client_for_tests.get("/material_groups")
        assert response.status_code == 200

        data = [MaterialGroupLocalizedResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) >= 2
        assert data[0].id == g1.id
        assert data[0].name == "Standard Ropes"
        assert data[1].id == g2.id
        assert data[1].name == "Technical Fibers"

    @pytest.mark.asyncio
    async def test_get_all_material_groups_locale(
        self,
        client_for_tests,
        create_material_group_fixture,
        create_material_group_translation_fixture,
    ):
        """Получение списка групп материалов с немецкой локализацией (GER)."""
        g = await create_material_group_fixture(
            CreateMaterialGroupFixtureDTO(code="tech", name="Technical (EN)")
        )
        await create_material_group_translation_fixture(
            CreateMaterialGroupTranslationFixtureDTO(
                material_group_id=g.id,
                locale=Language.GER,
                name="Technische Fasern",
            )
        )

        response = await client_for_tests.get("/material_groups", params={"locale": "ger"})
        assert response.status_code == 200

        data = [MaterialGroupLocalizedResponseDTO.model_validate(item) for item in response.json()]
        matched = [item for item in data if item.id == g.id]
        assert len(matched) == 1
        assert matched[0].name == "Technische Fasern"

    @pytest.mark.asyncio
    async def test_get_material_group_by_id(
        self,
        client_for_tests,
        create_material_group_fixture,
    ):
        """Получение группы материалов по ID со всеми переводами."""
        group = await create_material_group_fixture()

        response = await client_for_tests.get(f"/material_groups/{group.id}")
        assert response.status_code == 200

        dto = MaterialGroupResponseDTO.model_validate(response.json())
        assert dto.id == group.id
        assert dto.code == group.code
        assert len(dto.translations) >= 1

    @pytest.mark.asyncio
    async def test_create_material_group(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание новой группы материалов администратором."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        req_data = MaterialGroupCreate(
            code="racing",
            is_active=True,
            translations=[
                MaterialGroupTranslationCreate(locale=Language.ENG, name="Racing Line"),
                MaterialGroupTranslationCreate(locale=Language.GER, name="Regatta Leinen"),
            ],
        )

        response = await client_for_tests.post(
            "/material_groups",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        dto = MaterialGroupResponseDTO.model_validate(response.json())
        assert dto.code == "racing"
        assert dto.index == 1
        assert len(dto.translations) == 2

        res = await session_db.execute(
            select(MaterialGroup).where(MaterialGroup.id == dto.id)
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_material_group(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Обновление характеристик группы материалов."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="old_code"))

        update_data = MaterialGroupUpdate(code="new_code", is_active=False)
        response = await client_for_tests.patch(
            f"/material_groups/{group.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = MaterialGroupResponseDTO.model_validate(response.json())
        assert dto.code == "new_code"
        assert dto.is_active is False

    @pytest.mark.asyncio
    async def test_reorder_material_group(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Перемещение группы материалов со сдвигом соседей."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        g1 = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="g1", index=1))
        g2 = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="g2", index=2))
        g3 = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="g3", index=3))

        response = await client_for_tests.patch(
            f"/material_groups/{g3.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=MaterialGroupUpdateIndexDTO(new_index=1).model_dump(),
        )
        assert response.status_code == 200

        resp_list = await client_for_tests.get("/material_groups")
        groups = [MaterialGroupLocalizedResponseDTO.model_validate(i) for i in resp_list.json()]
        ordered_ids = [item.id for item in groups if item.id in (g1.id, g2.id, g3.id)]
        assert ordered_ids == [g3.id, g1.id, g2.id]

    @pytest.mark.asyncio
    async def test_delete_material_group_success(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Удаление группы материалов при отсутствии зависимостей (правило 5.1)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        g1 = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="del_1", index=1))
        g2 = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="del_2", index=2))
        g3 = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="del_3", index=3))

        response = await client_for_tests.delete(
            f"/material_groups/{g2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(MaterialGroup).where(MaterialGroup.id == g2.id))
        assert res.scalar_one_or_none() is None

        # Проверка сдвига g3: был 3, должен стать 2
        res_g3 = await session_db.execute(select(MaterialGroup).where(MaterialGroup.id == g3.id))
        item_g3 = res_g3.scalar_one()
        assert item_g3.index == 2

    @pytest.mark.asyncio
    async def test_add_translation(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Добавление перевода к группе материалов."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(locale=Language.ENG, name="Basic"))

        req_data = MaterialGroupTranslationCreate(locale=Language.GER, name="Basis")
        response = await client_for_tests.post(
            f"/material_groups/{group.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        dto = MaterialGroupTranslationResponseDTO.model_validate(response.json())
        assert dto.locale == Language.GER
        assert dto.name == "Basis"

    @pytest.mark.asyncio
    async def test_update_translation(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_translation_fixture,
    ):
        """Обновление перевода группы материалов."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        trans = await create_material_group_translation_fixture()

        update_data = MaterialGroupTranslationUpdate(name="Updated Name")
        response = await client_for_tests.patch(
            f"/material_groups/translations/{trans.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = MaterialGroupTranslationResponseDTO.model_validate(response.json())
        assert dto.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_translation_success(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
        create_material_group_translation_fixture,
    ):
        """Удаление перевода, если он не единственный (правило 5.1)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()
        t2 = await create_material_group_translation_fixture(
            CreateMaterialGroupTranslationFixtureDTO(material_group_id=group.id, locale=Language.GER)
        )

        response = await client_for_tests.delete(
            f"/material_groups/translations/{t2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(MaterialGroupTranslation).where(MaterialGroupTranslation.id == t2.id)
        )
        assert res.scalar_one_or_none() is None


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_create_material_group_unauthorized(
        self,
        client_for_tests,
    ):
        """Создание без токена -> 401."""
        req_data = MaterialGroupCreate(
            code="unauth",
            translations=[MaterialGroupTranslationCreate(locale=Language.ENG, name="Test")],
        )
        response = await client_for_tests.post("/material_groups", json=req_data.model_dump())
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_material_group_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание обычным юзером -> 403."""
        user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))
        req_data = MaterialGroupCreate(
            code="forbidden",
            translations=[MaterialGroupTranslationCreate(locale=Language.ENG, name="Test")],
        )
        response = await client_for_tests.post(
            "/material_groups",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_material_group_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Попытка создания группы с занятым кодом -> 409."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture(CreateMaterialGroupFixtureDTO(code="dup_code"))

        req_data = MaterialGroupCreate(
            code="dup_code",
            translations=[MaterialGroupTranslationCreate(locale=Language.ENG, name="Duplicate")],
        )
        response = await client_for_tests.post(
            "/material_groups",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_material_group_not_found(
        self,
        client_for_tests,
    ):
        """Запрос несуществующей группы материалов -> 404."""
        response = await client_for_tests.get("/material_groups/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_material_group_with_dependencies(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
        create_rope_product_fixture,
    ):
        """Запрет удаления группы материалов при наличии привязанных веревок (правило 5.1 -> 400)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()
        # Создаем веревку, привязанную к этой группе
        await create_rope_product_fixture(CreateRopeProductFixtureDTO(material_group_id=group.id))

        response = await client_for_tests.delete(
            f"/material_groups/{group.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_last_translation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Запрет удаления последнего оставшегося перевода (правило 5.1 -> 400)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()
        last_trans_id = group.translations[0].id

        response = await client_for_tests.delete(
            f"/material_groups/translations/{last_trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
