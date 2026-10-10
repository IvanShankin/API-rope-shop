import pytest
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.material_groups.fixtures.models_dto import CreateMaterialGroupFixtureDTO
from tests.modules.materials.fixtures.models_dto import (
    CreateMaterialFixtureDTO,
    CreateMaterialTranslationFixtureDTO,
)
from src.modules.materials.models import Material, MaterialTranslation
from src.modules.materials.models_dto import (
    MaterialCreate,
    MaterialUpdate,
    MaterialUpdateIndexDTO,
    MaterialResponseDTO,
    MaterialLocalizedResponseDTO,
    MaterialTranslationCreate,
    MaterialTranslationUpdate,
    MaterialTranslationResponseDTO,
)


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_materials(
        self,
        client_for_tests,
        create_material_group_fixture,
        create_material_fixture,
    ):
        """Получение списка материалов с локализацией по умолчанию (ENG) и фильтрацией по группе."""
        group = await create_material_group_fixture()
        other_group = await create_material_group_fixture()

        m1 = await create_material_fixture(
            CreateMaterialFixtureDTO(
                material_group_id=group.id,
                code="mat_1",
                name="Polyester",
                index=1,
            )
        )
        m2 = await create_material_fixture(
            CreateMaterialFixtureDTO(
                material_group_id=group.id,
                code="mat_2",
                name="Dyneema",
                index=2,
            )
        )
        # Material in another group
        await create_material_fixture(
            CreateMaterialFixtureDTO(
                material_group_id=other_group.id,
                code="mat_other",
                name="Nylon",
            )
        )

        response = await client_for_tests.get(
            "/materials",
            params={"material_group_id": group.id},
        )
        assert response.status_code == 200

        data = [MaterialLocalizedResponseDTO.model_validate(item) for item in response.json()]
        assert len(data) == 2
        assert data[0].id == m1.id
        assert data[0].name == "Polyester"
        assert data[1].id == m2.id
        assert data[1].name == "Dyneema"

    @pytest.mark.asyncio
    async def test_get_all_materials_locale(
        self,
        client_for_tests,
        create_material_fixture,
        create_material_translation_fixture,
    ):
        """Получение списка материалов с немецкой локализацией (GER)."""
        mat = await create_material_fixture(
            CreateMaterialFixtureDTO(code="poly", name="Polyester (EN)")
        )
        await create_material_translation_fixture(
            CreateMaterialTranslationFixtureDTO(
                material_id=mat.id,
                locale=Language.GER,
                name="Polyester (DE)",
            )
        )

        response = await client_for_tests.get("/materials", params={"locale": "ger"})
        assert response.status_code == 200

        data = [MaterialLocalizedResponseDTO.model_validate(item) for item in response.json()]
        matched = [item for item in data if item.id == mat.id]
        assert len(matched) == 1
        assert matched[0].name == "Polyester (DE)"

    @pytest.mark.asyncio
    async def test_get_all_materials_filter_is_active(
        self,
        client_for_tests,
        create_material_group_fixture,
        create_material_fixture,
    ):
        """Фильтрация материалов по флагу is_active."""
        group = await create_material_group_fixture()
        m_active = await create_material_fixture(
            CreateMaterialFixtureDTO(material_group_id=group.id, is_active=True)
        )
        m_inactive = await create_material_fixture(
            CreateMaterialFixtureDTO(material_group_id=group.id, is_active=False)
        )

        resp_active = await client_for_tests.get(
            "/materials",
            params={"material_group_id": group.id, "is_active": True},
        )
        assert resp_active.status_code == 200
        active_ids = [item["id"] for item in resp_active.json()]
        assert m_active.id in active_ids
        assert m_inactive.id not in active_ids

    @pytest.mark.asyncio
    async def test_get_material_by_id(
        self,
        client_for_tests,
        create_material_fixture,
    ):
        """Получение материала по ID со всеми переводами."""
        material = await create_material_fixture()

        response = await client_for_tests.get(f"/materials/{material.id}")
        assert response.status_code == 200

        dto = MaterialResponseDTO.model_validate(response.json())
        assert dto.id == material.id
        assert dto.code == material.code
        assert dto.material_group_id == material.material_group_id
        assert len(dto.translations) >= 1

    @pytest.mark.asyncio
    async def test_create_material(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Создание нового материала администратором."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()

        req_data = MaterialCreate(
            material_group_id=group.id,
            code="vectran_fibers",
            is_active=True,
            translations=[
                MaterialTranslationCreate(locale=Language.ENG, name="Vectran Fibers"),
                MaterialTranslationCreate(locale=Language.GER, name="Vectran Fasern"),
            ],
        )

        response = await client_for_tests.post(
            "/materials",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        dto = MaterialResponseDTO.model_validate(response.json())
        assert dto.code == "vectran_fibers"
        assert dto.material_group_id == group.id
        assert dto.index == 1
        assert len(dto.translations) == 2

        res = await session_db.execute(
            select(Material).where(Material.id == dto.id)
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_material(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_fixture,
    ):
        """Обновление атрибутов материала."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        material = await create_material_fixture(CreateMaterialFixtureDTO(code="old_mat_code"))

        update_data = MaterialUpdate(code="new_mat_code", is_active=False)
        response = await client_for_tests.patch(
            f"/materials/{material.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = MaterialResponseDTO.model_validate(response.json())
        assert dto.code == "new_mat_code"
        assert dto.is_active is False

    @pytest.mark.asyncio
    async def test_update_material_change_group(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
        create_material_fixture,
    ):
        """Перенос материала в другую группу с пересчетом индексов."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        g1 = await create_material_group_fixture()
        g2 = await create_material_group_fixture()

        m1_g1 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=g1.id, index=1))
        m2_g1 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=g1.id, index=2))
        m1_g2 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=g2.id, index=1))

        # Переносим m1_g1 во вторую группу
        response = await client_for_tests.patch(
            f"/materials/{m1_g1.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"material_group_id": g2.id},
        )
        assert response.status_code == 200
        dto = MaterialResponseDTO.model_validate(response.json())
        assert dto.material_group_id == g2.id
        # В группе g2 был m1_g2 с индексом 1, поэтому перенесенный должен стать индексом 2
        assert dto.index == 2

        # В группе g1 m2_g1 должен сдвинуться с индекса 2 на индекс 1
        res = await session_db.execute(select(Material).where(Material.id == m2_g1.id))
        updated_m2 = res.scalar_one()
        assert updated_m2.index == 1

    @pytest.mark.asyncio
    async def test_reorder_material(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
        create_material_fixture,
    ):
        """Изменение позиции материала внутри группы со сдвигом соседей."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()
        m1 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id, index=1))
        m2 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id, index=2))
        m3 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id, index=3))

        response = await client_for_tests.patch(
            f"/materials/{m3.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=MaterialUpdateIndexDTO(new_index=1).model_dump(),
        )
        assert response.status_code == 200

        resp_list = await client_for_tests.get("/materials", params={"material_group_id": group.id})
        items = [MaterialLocalizedResponseDTO.model_validate(i) for i in resp_list.json()]
        ordered_ids = [item.id for item in items if item.id in (m1.id, m2.id, m3.id)]
        assert ordered_ids == [m3.id, m1.id, m2.id]

    @pytest.mark.asyncio
    async def test_delete_material_success(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
        create_material_fixture,
    ):
        """Удаление материала и сдвиг оставшихся индексов внутри группы."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()
        m1 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id, index=1))
        m2 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id, index=2))
        m3 = await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id, index=3))

        response = await client_for_tests.delete(
            f"/materials/{m2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(Material).where(Material.id == m2.id))
        assert res.scalar_one_or_none() is None

        # Проверка сдвига m3: был 3, должен стать 2
        res_m3 = await session_db.execute(select(Material).where(Material.id == m3.id))
        item_m3 = res_m3.scalar_one()
        assert item_m3.index == 2

    @pytest.mark.asyncio
    async def test_add_translation(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_fixture,
    ):
        """Добавление перевода к материалу."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        material = await create_material_fixture(CreateMaterialFixtureDTO(locale=Language.ENG, name="Basic Mat"))

        req_data = MaterialTranslationCreate(locale=Language.GER, name="Basis Mat")
        response = await client_for_tests.post(
            f"/materials/{material.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 201

        dto = MaterialTranslationResponseDTO.model_validate(response.json())
        assert dto.locale == Language.GER
        assert dto.name == "Basis Mat"

    @pytest.mark.asyncio
    async def test_update_translation(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_translation_fixture,
    ):
        """Обновление перевода материала."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        trans = await create_material_translation_fixture()

        update_data = MaterialTranslationUpdate(name="Updated Mat Name")
        response = await client_for_tests.patch(
            f"/materials/translations/{trans.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = MaterialTranslationResponseDTO.model_validate(response.json())
        assert dto.name == "Updated Mat Name"

    @pytest.mark.asyncio
    async def test_delete_translation_success(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_material_fixture,
        create_material_translation_fixture,
    ):
        """Удаление перевода, если он не единственный (правило 5.1)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        material = await create_material_fixture()
        t2 = await create_material_translation_fixture(
            CreateMaterialTranslationFixtureDTO(material_id=material.id, locale=Language.GER)
        )

        response = await client_for_tests.delete(
            f"/materials/translations/{t2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(MaterialTranslation).where(MaterialTranslation.id == t2.id)
        )
        assert res.scalar_one_or_none() is None


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_create_material_unauthorized(
        self,
        client_for_tests,
        create_material_group_fixture,
    ):
        """Создание без токена -> 401."""
        group = await create_material_group_fixture()
        req_data = MaterialCreate(
            material_group_id=group.id,
            code="unauth",
            translations=[MaterialTranslationCreate(locale=Language.ENG, name="Test")],
        )
        response = await client_for_tests.post("/materials", json=req_data.model_dump())
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_material_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
    ):
        """Создание обычным юзером -> 403."""
        user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))
        group = await create_material_group_fixture()
        req_data = MaterialCreate(
            material_group_id=group.id,
            code="forbidden",
            translations=[MaterialTranslationCreate(locale=Language.ENG, name="Test")],
        )
        response = await client_for_tests.post(
            "/materials",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_material_nonexistent_group(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание материала с несуществующей группой -> 404."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        req_data = MaterialCreate(
            material_group_id=999999,
            code="no_group",
            translations=[MaterialTranslationCreate(locale=Language.ENG, name="Test")],
        )
        response = await client_for_tests.post(
            "/materials",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_material_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
        create_material_fixture,
    ):
        """Создание материала с занятым кодом -> 409."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()
        await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id, code="dup_mat"))

        req_data = MaterialCreate(
            material_group_id=group.id,
            code="dup_mat",
            translations=[MaterialTranslationCreate(locale=Language.ENG, name="Duplicate")],
        )
        response = await client_for_tests.post(
            "/materials",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_material_not_found(
        self,
        client_for_tests,
    ):
        """Запрос несуществующего материала -> 404."""
        response = await client_for_tests.get("/materials/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_last_translation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_fixture,
    ):
        """Запрет удаления последнего оставшегося перевода (правило 5.1 -> 400)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        material = await create_material_fixture()
        last_trans_id = material.translations[0].id

        response = await client_for_tests.delete(
            f"/materials/translations/{last_trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_material_group_cannot_be_deleted_with_materials(
        self,
        client_for_tests,
        create_user_fixture,
        create_material_group_fixture,
        create_material_fixture,
    ):
        """Запрет удаления группы материалов при наличии привязанного материала (правило 5.1 -> 400)."""
        admin_user, access_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        group = await create_material_group_fixture()
        await create_material_fixture(CreateMaterialFixtureDTO(material_group_id=group.id))

        response = await client_for_tests.delete(
            f"/material_groups/{group.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
