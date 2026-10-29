import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.colors.fixtures.models_dto import (
    CreateColorFixtureDTO,
    CreateColorTranslationFixtureDTO,
)
from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from src.modules.colors.models import Color, ColorTranslation
from src.modules.colors.models_dto import (
    ColorResponseDTO,
    ColorLocalizedResponseDTO,
    ColorCreate,
    ColorUpdate,
    ColorUpdateIndexDTO,
    ColorTranslationCreate,
    ColorTranslationUpdate,
    ColorTranslationResponseDTO,
)
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_colors(
        self,
        client_for_tests,
        create_color_fixture,
    ):
        color_1 = await create_color_fixture(
            CreateColorFixtureDTO(code="red_01", name="Red")
        )
        color_2 = await create_color_fixture(
            CreateColorFixtureDTO(code="blue_01", name="Blue")
        )

        response = await client_for_tests.get("/colors")
        assert response.status_code == 200

        data = [
            ColorLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) >= 2

        ids = [item.id for item in data]
        assert color_1.id in ids
        assert color_2.id in ids

        found = next(item for item in data if item.id == color_1.id)
        assert found.code == "red_01"
        assert found.name == "Red"

    @pytest.mark.asyncio
    async def test_get_all_colors_filter_is_active(
        self,
        client_for_tests,
        create_color_fixture,
    ):
        active_color = await create_color_fixture(
            CreateColorFixtureDTO(is_active=True)
        )
        inactive_color = await create_color_fixture(
            CreateColorFixtureDTO(is_active=False)
        )

        resp_active = await client_for_tests.get("/colors", params={"is_active": "true"})
        assert resp_active.status_code == 200
        active_items = [
            ColorLocalizedResponseDTO.model_validate(item)
            for item in resp_active.json()
        ]
        active_ids = [item.id for item in active_items]
        assert active_color.id in active_ids
        assert inactive_color.id not in active_ids

        resp_inactive = await client_for_tests.get("/colors", params={"is_active": "false"})
        assert resp_inactive.status_code == 200
        inactive_items = [
            ColorLocalizedResponseDTO.model_validate(item)
            for item in resp_inactive.json()
        ]
        inactive_ids = [item.id for item in inactive_items]
        # Анонимный пользователь не должен получать неактивные цвета
        assert inactive_color.id not in inactive_ids
        assert active_color.id in inactive_ids

    @pytest.mark.asyncio
    async def test_get_all_colors_admin_sees_inactive(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        """Администратор может получать неактивные цвета через фильтр."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        active_color = await create_color_fixture(
            CreateColorFixtureDTO(is_active=True)
        )
        inactive_color = await create_color_fixture(
            CreateColorFixtureDTO(is_active=False)
        )

        resp_inactive = await client_for_tests.get(
            "/colors",
            params={"is_active": "false"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp_inactive.status_code == 200
        inactive_items = [
            ColorLocalizedResponseDTO.model_validate(item)
            for item in resp_inactive.json()
        ]
        inactive_ids = [item.id for item in inactive_items]
        assert inactive_color.id in inactive_ids
        assert active_color.id not in inactive_ids

    @pytest.mark.asyncio
    async def test_get_all_colors_locale(
        self,
        client_for_tests,
        create_color_fixture,
        create_color_translation_fixture,
    ):
        color = await create_color_fixture(
            CreateColorFixtureDTO(locale=Language.ENG, name="Green")
        )
        await create_color_translation_fixture(
            CreateColorTranslationFixtureDTO(
                color_id=color.id,
                locale=Language.GER,
                name="Grün",
            )
        )

        response = await client_for_tests.get("/colors", params={"locale": "ger"})
        assert response.status_code == 200

        data = [
            ColorLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        found = next(item for item in data if item.id == color.id)
        assert found.name == "Grün"

    @pytest.mark.asyncio
    async def test_get_color_by_id(
        self,
        client_for_tests,
        create_color_fixture,
    ):
        color = await create_color_fixture(CreateColorFixtureDTO(code="black_01", name="Black"))

        response = await client_for_tests.get(f"/colors/{color.id}")
        assert response.status_code == 200

        resp_dto = ColorResponseDTO.model_validate(response.json())
        assert resp_dto.id == color.id
        assert resp_dto.code == "black_01"
        assert len(resp_dto.translations) >= 1
        assert comparison_models(color, resp_dto, keys_not_checked=["translations"])

    @pytest.mark.asyncio
    async def test_create_color(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = ColorCreate(
            code="cyan_neon",
            hex="#00FFFF",
            index=5,
            is_active=True,
            translations=[
                ColorTranslationCreate(
                    locale=Language.ENG,
                    name="Neon Cyan",
                ),
                ColorTranslationCreate(
                    locale=Language.GER,
                    name="Neon Cyan Deutsch",
                ),
            ],
        )

        response = await client_for_tests.post(
            "/colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = ColorResponseDTO.model_validate(response.json())
        assert resp_dto.code == "cyan_neon"
        assert resp_dto.hex == "#00FFFF"
        assert resp_dto.index == 5
        assert resp_dto.is_active is True
        assert len(resp_dto.translations) == 2

        # Проверяем в БД
        res = await session_db.execute(
            select(Color)
            .where(Color.id == resp_dto.id)
            .options(selectinload(Color.translations))
        )
        color_from_db = res.scalar_one_or_none()
        assert color_from_db is not None
        assert comparison_models(resp_dto, color_from_db, keys_not_checked=["translations"])
        assert len(color_from_db.translations) == 2

    @pytest.mark.asyncio
    async def test_update_color(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO(index=1, hex="#111111"))

        update_data = ColorUpdate(
            hex="#222222",
            is_active=False,
        )

        response = await client_for_tests.patch(
            f"/colors/{color.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True, mode="json"),
        )
        assert response.status_code == 200

        updated_dto = ColorResponseDTO.model_validate(response.json())
        assert updated_dto.hex == "#222222"
        assert updated_dto.index == 1
        assert updated_dto.is_active is False

        session_db.expire_all()
        res = await session_db.execute(select(Color).where(Color.id == color.id))
        db_item = res.scalar_one_or_none()
        assert db_item is not None
        assert db_item.hex == "#222222"
        assert db_item.index == 1
        assert db_item.is_active is False

    @pytest.mark.asyncio
    async def test_update_color_index(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        """Тест перемещения индекса (reorder) с автоматическим сдвигом соседей."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        c0 = await create_color_fixture(CreateColorFixtureDTO(code="c0", index=0))
        c1 = await create_color_fixture(CreateColorFixtureDTO(code="c1", index=1))
        c2 = await create_color_fixture(CreateColorFixtureDTO(code="c2", index=2))
        c3 = await create_color_fixture(CreateColorFixtureDTO(code="c3", index=3))

        # 1. Перемещаем c3 (был index=3) на index=1 (сдвиг вверх/вперед)
        # Записи с 1 <= index < 3 (c1 и c2) должны сдвинуться на +1: c1 -> 2, c2 -> 3
        req_data = ColorUpdateIndexDTO(new_index=1)
        response = await client_for_tests.patch(
            f"/colors/{c3.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json=req_data.model_dump(),
        )
        assert response.status_code == 200

        updated_dto = ColorResponseDTO.model_validate(response.json())
        assert updated_dto.id == c3.id
        assert updated_dto.index == 1

        # Проверяем в БД все индексы
        session_db.expire_all()
        db_c0 = (await session_db.execute(select(Color).where(Color.id == c0.id))).scalar_one()
        db_c1 = (await session_db.execute(select(Color).where(Color.id == c1.id))).scalar_one()
        db_c2 = (await session_db.execute(select(Color).where(Color.id == c2.id))).scalar_one()
        db_c3 = (await session_db.execute(select(Color).where(Color.id == c3.id))).scalar_one()

        assert db_c0.index == 0
        assert db_c3.index == 1
        assert db_c1.index == 2
        assert db_c2.index == 3

        # 2. Перемещаем c0 (был index=0) на index=2 (сдвиг вниз/назад)
        # Записи с 0 < index <= 2 (c3 c index=1 и c1 c index=2) должны сдвинуться на -1: c3 -> 0, c1 -> 1
        response_2 = await client_for_tests.patch(
            f"/colors/{c0.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response_2.status_code == 200

        updated_dto_2 = ColorResponseDTO.model_validate(response_2.json())
        assert updated_dto_2.id == c0.id
        assert updated_dto_2.index == 2

        session_db.expire_all()
        db_c0 = (await session_db.execute(select(Color).where(Color.id == c0.id))).scalar_one()
        db_c1 = (await session_db.execute(select(Color).where(Color.id == c1.id))).scalar_one()
        db_c2 = (await session_db.execute(select(Color).where(Color.id == c2.id))).scalar_one()
        db_c3 = (await session_db.execute(select(Color).where(Color.id == c3.id))).scalar_one()

        assert db_c3.index == 0
        assert db_c1.index == 1
        assert db_c0.index == 2
        assert db_c2.index == 3

    @pytest.mark.asyncio
    async def test_update_color_index_same_value(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        """Тест перемещения индекса на то же самое значение (no-op)."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO(index=5))

        response = await client_for_tests.patch(
            f"/colors/{color.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 5},
        )
        assert response.status_code == 200

        updated_dto = ColorResponseDTO.model_validate(response.json())
        assert updated_dto.index == 5

    @pytest.mark.asyncio
    async def test_delete_color(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO())

        response = await client_for_tests.delete(
            f"/colors/{color.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(select(Color).where(Color.id == color.id))
        assert res.scalar_one_or_none() is None

        # Проверяем каскадное удаление переводов
        res_trans = await session_db.execute(
            select(ColorTranslation).where(ColorTranslation.color_id == color.id)
        )
        assert len(res_trans.scalars().all()) == 0

    @pytest.mark.asyncio
    async def test_add_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO(locale=Language.ENG))

        trans_data = ColorTranslationCreate(
            locale=Language.GER,
            name="Deutscher Name",
        )

        response = await client_for_tests.post(
            f"/colors/{color.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 201

        resp_dto = ColorTranslationResponseDTO.model_validate(response.json())
        assert resp_dto.locale == Language.GER
        assert resp_dto.name == "Deutscher Name"
        assert resp_dto.color_id == color.id

        # Проверяем в БД
        res = await session_db.execute(
            select(ColorTranslation).where(ColorTranslation.id == resp_dto.id)
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO(name="Original"))
        trans_id = color.translations[0].id

        update_data = ColorTranslationUpdate(
            name="Updated Name",
        )

        response = await client_for_tests.patch(
            f"/colors/translations/{trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        updated_dto = ColorTranslationResponseDTO.model_validate(response.json())
        assert updated_dto.name == "Updated Name"

        res = await session_db.execute(
            select(ColorTranslation).where(ColorTranslation.id == trans_id)
        )
        db_trans = res.scalar_one_or_none()
        assert db_trans is not None
        assert db_trans.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
        create_color_translation_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO(locale=Language.ENG))
        extra_trans = await create_color_translation_fixture(
            CreateColorTranslationFixtureDTO(color_id=color.id, locale=Language.GER)
        )

        response = await client_for_tests.delete(
            f"/colors/translations/{extra_trans.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(ColorTranslation).where(ColorTranslation.id == extra_trans.id)
        )
        assert res.scalar_one_or_none() is None


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_create_color_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )

        create_data = ColorCreate(
            code="forbidden_color",
            index=1,
            translations=[
                ColorTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_color_unauthorized(
        self,
        client_for_tests,
    ):
        create_data = ColorCreate(
            code="unauth_color",
            index=1,
            translations=[
                ColorTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/colors",
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_color_without_translations(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        create_data = {
            "code": "no_trans_color",
            "index": 1,
            "translations": [],
        }

        response = await client_for_tests.post(
            "/colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_color_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        await create_color_fixture(CreateColorFixtureDTO(code="duplicate_code"))

        create_data = ColorCreate(
            code="duplicate_code",
            index=2,
            translations=[
                ColorTranslationCreate(locale=Language.ENG, name="Test"),
            ],
        )

        response = await client_for_tests.post(
            "/colors",
            headers={"Authorization": f"Bearer {access_token}"},
            json=create_data.model_dump(mode="json"),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_color_not_found(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.get("/colors/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_color_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/colors/99999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"hex": "#123456"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_color_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color_1 = await create_color_fixture(CreateColorFixtureDTO(code="code_one"))
        color_2 = await create_color_fixture(CreateColorFixtureDTO(code="code_two"))

        response = await client_for_tests.patch(
            f"/colors/{color_2.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"code": "code_one"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_color_index_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        regular_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        color = await create_color_fixture(CreateColorFixtureDTO())

        response = await client_for_tests.patch(
            f"/colors/{color.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_color_index_unauthorized(
        self,
        client_for_tests,
        create_color_fixture,
    ):
        color = await create_color_fixture(CreateColorFixtureDTO())

        response = await client_for_tests.patch(
            f"/colors/{color.id}/index",
            json={"new_index": 2},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_color_index_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/colors/99999/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": 2},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_color_index_validation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO())

        # new_index < 0 should fail with 422 Unprocessable Entity
        response = await client_for_tests.patch(
            f"/colors/{color.id}/index",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"new_index": -1},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_color_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/colors/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_color_has_dependencies(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
        create_rope_product_fixture,
        create_rope_product_color_fixture,
    ):
        """Попытка удаления цвета, привязанного к товару-веревке -> 400 Bad Request."""
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO())
        product = await create_rope_product_fixture()
        await create_rope_product_color_fixture(
            CreateRopeProductColorFixtureDTO(
                product_id=product.product_id,
                color_id=color.id,
                index=1,
            )
        )

        response = await client_for_tests.delete(
            f"/colors/{color.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert "referenced by rope products" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_translation_color_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        trans_data = ColorTranslationCreate(
            locale=Language.GER,
            name="German Name",
        )

        response = await client_for_tests.post(
            "/colors/99999/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_translation_duplicate_locale(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO(locale=Language.ENG))

        trans_data = ColorTranslationCreate(
            locale=Language.ENG,
            name="Duplicate English",
        )

        response = await client_for_tests.post(
            f"/colors/{color.id}/translations",
            headers={"Authorization": f"Bearer {access_token}"},
            json=trans_data.model_dump(mode="json"),
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_translation_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.patch(
            "/colors/translations/99999",
            headers={"Authorization": f"Bearer {access_token}"},\
            json={"name": "New Name"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_translation_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        response = await client_for_tests.delete(
            "/colors/translations/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_last_translation_error(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        admin_user, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO())
        only_trans_id = color.translations[0].id

        response = await client_for_tests.delete(
            f"/colors/translations/{only_trans_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_inactive_color_anonymous_returns_404(
        self,
        client_for_tests,
        create_color_fixture,
    ):
        """Анонимный запрос к неактивному цвету по ID возвращает 404."""
        color = await create_color_fixture(CreateColorFixtureDTO(is_active=False))
        resp_id = await client_for_tests.get(f"/colors/{color.id}")
        assert resp_id.status_code == 404

    @pytest.mark.asyncio
    async def test_get_inactive_color_admin_returns_200(
        self,
        client_for_tests,
        create_user_fixture,
        create_color_fixture,
    ):
        """Администратор имеет доступ к неактивному цвету по ID."""
        _, access_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        color = await create_color_fixture(CreateColorFixtureDTO(is_active=False))
        headers = {"Authorization": f"Bearer {access_token}"}
        resp_id = await client_for_tests.get(f"/colors/{color.id}", headers=headers)
        assert resp_id.status_code == 200
