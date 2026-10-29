import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.product_application.models import (
    ProductApplication,
    ProductApplicationTranslation,
    ProductAssignedApplication,
)
from src.modules.product_application.models_dto import (
    AssignApplicationToProductDTO,
    ProductApplicationCreate,
    ProductApplicationLocalizedResponseDTO,
    ProductApplicationResponseDTO,
    ProductApplicationTranslationCreate,
    ProductApplicationTranslationResponseDTO,
    ProductApplicationTranslationUpdate,
    ProductApplicationUpdate,
    ProductApplicationUpdateIndexDTO,
    ProductAssignedApplicationResponseDTO,
)
from src.modules.users.models import UserRole
from tests.helpers.functions import comparison_models
from tests.modules.product_application.fixtures.models_dto import (
    CreateProductApplicationFixtureDTO,
    CreateProductApplicationTranslationFixtureDTO,
    CreateProductAssignedApplicationFixtureDTO,
)
from tests.modules.products.fixtures.models_dto import CreateProductFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_all_applications_with_locale(
        self,
        client_for_tests,
        create_product_application_fixture,
        create_product_application_translation_fixture,
    ):
        """Получение всех назначений с локализацией (ger)."""
        app_1 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="winch", name="Winch Rope", locale=Language.ENG)
        )
        await create_product_application_translation_fixture(
            CreateProductApplicationTranslationFixtureDTO(
                application_id=app_1.id,
                locale=Language.GER,
                name="Windenseil",
            )
        )

        app_2 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="sheet", name="Sheets", locale=Language.ENG)
        )
        await create_product_application_translation_fixture(
            CreateProductApplicationTranslationFixtureDTO(
                application_id=app_2.id,
                locale=Language.GER,
                name="Schoten",
            )
        )

        response = await client_for_tests.get("/product_applications?locale=ger")
        assert response.status_code == 200

        data = [
            ProductApplicationLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) >= 2

        found_1 = next(item for item in data if item.id == app_1.id)
        assert found_1.code == "winch"
        assert found_1.name == "Windenseil"

        found_2 = next(item for item in data if item.id == app_2.id)
        assert found_2.code == "sheet"
        assert found_2.name == "Schoten"

    @pytest.mark.asyncio
    async def test_get_all_applications_without_locale(
        self,
        client_for_tests,
        create_product_application_fixture,
    ):
        """Получение всех назначений без указания локали (полный список с переводами)."""
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="halyard", name="Halyards", locale=Language.ENG)
        )

        response = await client_for_tests.get("/product_applications")
        assert response.status_code == 200

        data = [
            ProductApplicationResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) >= 1

        found = next(item for item in data if item.id == app.id)
        assert found.code == "halyard"
        assert len(found.translations) >= 1
        assert found.translations[0].locale == Language.ENG
        assert found.translations[0].name == "Halyards"

    @pytest.mark.asyncio
    async def test_get_all_applications_filter_is_active(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """Фильтрация назначений по активности (is_active). Неактивные доступны только админу."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        active_app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="active_app", is_active=True)
        )
        inactive_app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="inactive_app", is_active=False)
        )

        resp_active = await client_for_tests.get("/product_applications", params={"is_active": "true"})
        assert resp_active.status_code == 200
        active_items = [
            ProductApplicationResponseDTO.model_validate(item)
            for item in resp_active.json()
        ]
        active_ids = [item.id for item in active_items]
        assert active_app.id in active_ids
        assert inactive_app.id not in active_ids

        # Админ может запросить неактивные
        resp_inactive = await client_for_tests.get(
            "/product_applications",
            params={"is_active": "false"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_inactive.status_code == 200
        inactive_items = [
            ProductApplicationResponseDTO.model_validate(item)
            for item in resp_inactive.json()
        ]
        inactive_ids = [item.id for item in inactive_items]
        assert inactive_app.id in inactive_ids
        assert active_app.id not in inactive_ids

        # Аноним при ?is_active=false всё равно получает только активные
        resp_anon = await client_for_tests.get("/product_applications", params={"is_active": "false"})
        assert resp_anon.status_code == 200
        anon_ids = [item["id"] for item in resp_anon.json()]
        assert inactive_app.id not in anon_ids
        assert active_app.id in anon_ids

    @pytest.mark.asyncio
    async def test_get_all_applications_pagination(
        self,
        client_for_tests,
        create_product_application_fixture,
    ):
        """Пагинация списка назначений (skip, limit)."""
        for i in range(3):
            await create_product_application_fixture(
                CreateProductApplicationFixtureDTO(code=f"page_app_{i}", index=i)
            )

        resp = await client_for_tests.get("/product_applications", params={"skip": 1, "limit": 1})
        assert resp.status_code == 200
        items = [
            ProductApplicationResponseDTO.model_validate(item)
            for item in resp.json()
        ]
        assert len(items) == 1
        assert items[0].code == "page_app_1"

    @pytest.mark.asyncio
    async def test_get_application_by_id(
        self,
        client_for_tests,
        create_product_application_fixture,
    ):
        """Получение назначения по ID."""
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="mooring", name="Mooring Ropes")
        )

        response = await client_for_tests.get(f"/product_applications/{app.id}")
        assert response.status_code == 200

        resp_dto = ProductApplicationResponseDTO.model_validate(response.json())
        assert resp_dto.id == app.id
        assert resp_dto.code == "mooring"
        assert comparison_models(app, resp_dto, keys_not_checked=["translations"])

    @pytest.mark.asyncio
    async def test_get_application_by_code(
        self,
        client_for_tests,
        create_product_application_fixture,
    ):
        """Получение назначения по уникальному коду."""
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="climbing", name="Climbing")
        )

        response = await client_for_tests.get(f"/product_applications/by-code/climbing")
        assert response.status_code == 200

        resp_dto = ProductApplicationResponseDTO.model_validate(response.json())
        assert resp_dto.id == app.id
        assert resp_dto.code == "climbing"

    @pytest.mark.asyncio
    async def test_create_application(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        """Создание нового назначения администратором."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )

        payload = {
            "code": "sling",
            "index": 10,
            "is_active": True,
            "translations": [
                {"locale": "eng", "name": "Slings"},
                {"locale": "rus", "name": "Стропы"},
            ],
        }

        response = await client_for_tests.post(
            "/product_applications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert response.status_code == 201

        resp_dto = ProductApplicationResponseDTO.model_validate(response.json())
        assert resp_dto.code == "sling"
        assert resp_dto.index == 10
        assert resp_dto.is_active is True
        assert len(resp_dto.translations) == 2

        # Проверяем в БД
        res = await session_db.execute(
            select(ProductApplication)
            .where(ProductApplication.id == resp_dto.id)
            .options(selectinload(ProductApplication.translations))
        )
        app_db = res.scalar_one_or_none()
        assert app_db is not None
        assert app_db.code == "sling"
        assert len(app_db.translations) == 2

    @pytest.mark.asyncio
    async def test_create_application_auto_index(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """Автоматическое присвоение index (max_index + 1), если index не передан."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="first_app", index=5)
        )

        payload = {
            "code": "second_app",
            "translations": [
                {"locale": "eng", "name": "Second App"},
            ],
        }

        response = await client_for_tests.post(
            "/product_applications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert response.status_code == 201

        resp_dto = ProductApplicationResponseDTO.model_validate(response.json())
        assert resp_dto.index == 6

    @pytest.mark.asyncio
    async def test_update_application(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """Обновление атрибутов назначения (code, is_active)."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="old_code", is_active=True)
        )

        update_payload = {
            "code": "new_code",
            "is_active": False,
        }

        response = await client_for_tests.patch(
            f"/product_applications/{app.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_payload,
        )
        assert response.status_code == 200

        resp_dto = ProductApplicationResponseDTO.model_validate(response.json())
        assert resp_dto.code == "new_code"
        assert resp_dto.is_active is False

        res = await session_db.execute(
            select(ProductApplication).where(ProductApplication.id == app.id)
        )
        app_db = res.scalar_one_or_none()
        assert app_db.code == "new_code"
        assert app_db.is_active is False

    @pytest.mark.asyncio
    async def test_reorder_application(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """Изменение порядка назначения со сдвигом соседей."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app_0 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="pos_0", index=0)
        )
        app_1 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="pos_1", index=1)
        )
        app_2 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="pos_2", index=2)
        )

        # Перемещаем app_2 на индекс 0
        response = await client_for_tests.patch(
            f"/product_applications/{app_2.id}/index",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_index": 0},
        )
        assert response.status_code == 200

        resp_dto = ProductApplicationResponseDTO.model_validate(response.json())
        assert resp_dto.index == 0

        # Проверяем, что соседи сдвинулись
        resp_0 = await client_for_tests.get(f"/product_applications/{app_0.id}")
        assert ProductApplicationResponseDTO.model_validate(resp_0.json()).index == 1

        resp_1 = await client_for_tests.get(f"/product_applications/{app_1.id}")
        assert ProductApplicationResponseDTO.model_validate(resp_1.json()).index == 2

    @pytest.mark.asyncio
    async def test_delete_application(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """Удаление назначения без зависимостей со сдвигом последующих индексов."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app_0 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="del_0", index=0)
        )
        app_1 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="del_1", index=1)
        )

        response = await client_for_tests.delete(
            f"/product_applications/{app_0.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        # Проверяем удаление в БД
        res = await session_db.execute(
            select(ProductApplication).where(ProductApplication.id == app_0.id)
        )
        assert res.scalar_one_or_none() is None

        # Проверяем сдвиг индекса у оставшегося
        resp_1 = await client_for_tests.get(f"/product_applications/{app_1.id}")
        assert ProductApplicationResponseDTO.model_validate(resp_1.json()).index == 0

    @pytest.mark.asyncio
    async def test_add_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """Добавление перевода для назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG, name="Original")
        )

        trans_payload = {
            "locale": "ger",
            "name": "Deutscher Name",
        }

        response = await client_for_tests.post(
            f"/product_applications/{app.id}/translations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=trans_payload,
        )
        assert response.status_code == 201

        resp_dto = ProductApplicationTranslationResponseDTO.model_validate(response.json())
        assert resp_dto.application_id == app.id
        assert resp_dto.locale == Language.GER
        assert resp_dto.name == "Deutscher Name"

        # Проверяем в БД
        res = await session_db.execute(
            select(ProductApplicationTranslation).where(
                ProductApplicationTranslation.id == resp_dto.id
            )
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """Обновление текста перевода назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG, name="Old Name")
        )

        response = await client_for_tests.patch(
            f"/product_applications/{app.id}/translations/eng",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "New Name"},
        )
        assert response.status_code == 200

        resp_dto = ProductApplicationTranslationResponseDTO.model_validate(response.json())
        assert resp_dto.name == "New Name"

        res = await session_db.execute(
            select(ProductApplicationTranslation).where(
                ProductApplicationTranslation.application_id == app.id,
                ProductApplicationTranslation.locale == Language.ENG,
            )
        )
        trans_db = res.scalar_one_or_none()
        assert trans_db.name == "New Name"

    @pytest.mark.asyncio
    async def test_delete_translation(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
        create_product_application_translation_fixture,
    ):
        """Удаление перевода (если у назначения остаётся хотя бы один)."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG, name="Eng Name")
        )
        ger_trans = await create_product_application_translation_fixture(
            CreateProductApplicationTranslationFixtureDTO(
                application_id=app.id,
                locale=Language.GER,
                name="Ger Name",
            )
        )

        response = await client_for_tests.delete(
            f"/product_applications/{app.id}/translations/ger",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(ProductApplicationTranslation).where(
                ProductApplicationTranslation.id == ger_trans.id
            )
        )
        assert res.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_assign_application_to_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_application_fixture,
    ):
        """Привязка назначения к товару администратором."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="winch_assign", name="Winch")
        )

        response = await client_for_tests.post(
            f"/product_applications/by-product/{product.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"application_id": app.id},
        )
        assert response.status_code == 201

        resp_dto = ProductAssignedApplicationResponseDTO.model_validate(response.json())
        assert resp_dto.product_id == product.id
        assert resp_dto.application_id == app.id
        assert resp_dto.application is not None
        assert resp_dto.application.code == "winch_assign"

        # Проверяем в БД
        res = await session_db.execute(
            select(ProductAssignedApplication).where(
                ProductAssignedApplication.product_id == product.id,
                ProductAssignedApplication.application_id == app.id,
            )
        )
        assert res.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_get_product_applications(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
    ):
        """Получение списка назначений товара с локализацией (публичный эндпоинт)."""
        product = await create_product_fixture()
        app_1 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="app_sheet", index=0, locale=Language.ENG, name="Sheet Eng")
        )
        app_2 = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="app_halyard", index=1, locale=Language.ENG, name="Halyard Eng")
        )

        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=product.id, application_id=app_1.id)
        )
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=product.id, application_id=app_2.id)
        )

        response = await client_for_tests.get(f"/product_applications/by-product/{product.id}?locale=eng")
        assert response.status_code == 200

        data = [
            ProductApplicationLocalizedResponseDTO.model_validate(item)
            for item in response.json()
        ]
        assert len(data) == 2
        assert data[0].code == "app_sheet"
        assert data[0].name == "Sheet Eng"
        assert data[1].code == "app_halyard"
        assert data[1].name == "Halyard Eng"

    @pytest.mark.asyncio
    async def test_unassign_application_from_product(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
    ):
        """Отвязка назначения от товара администратором."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        app = await create_product_application_fixture()
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=product.id, application_id=app.id)
        )

        response = await client_for_tests.delete(
            f"/product_applications/by-product/{product.id}/{app.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        res = await session_db.execute(
            select(ProductAssignedApplication).where(
                ProductAssignedApplication.product_id == product.id,
                ProductAssignedApplication.application_id == app.id,
            )
        )
        assert res.scalar_one_or_none() is None


class TestsForErrors:

    @pytest.mark.asyncio
    async def test_get_application_by_id_not_found(
        self,
        client_for_tests,
    ):
        """404: Назначение с несуществующим ID."""
        response = await client_for_tests.get("/product_applications/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_application_by_code_not_found(
        self,
        client_for_tests,
    ):
        """404: Назначение с несуществующим кодом."""
        response = await client_for_tests.get("/product_applications/by-code/non_existent_code")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_application_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """403: Обычный пользователь не имеет права создавать назначения."""
        _, user_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        payload = {
            "code": "forbidden_app",
            "translations": [{"locale": "eng", "name": "Forbidden"}],
        }
        response = await client_for_tests.post(
            "/product_applications",
            headers={"Authorization": f"Bearer {user_token}"},
            json=payload,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_application_unauthorized(
        self,
        client_for_tests,
    ):
        """401: Неавторизованный пользователь."""
        payload = {
            "code": "unauth_app",
            "translations": [{"locale": "eng", "name": "Unauth"}],
        }
        response = await client_for_tests.post(
            "/product_applications",
            json=payload,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_application_empty_translations(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """422: Ошибка валидации при пустом списке переводов."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        payload = {
            "code": "no_trans",
            "translations": [],
        }
        response = await client_for_tests.post(
            "/product_applications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_application_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """409: Попытка создать назначение с уже существующим кодом."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="dup_code")
        )

        payload = {
            "code": "dup_code",
            "translations": [{"locale": "eng", "name": "Duplicate"}],
        }
        response = await client_for_tests.post(
            "/product_applications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_application_duplicate_locales(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """409: Дублирующиеся локали в теле создания назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        payload = {
            "code": "dup_locales",
            "translations": [
                {"locale": "eng", "name": "Eng 1"},
                {"locale": "eng", "name": "Eng 2"},
            ],
        }
        response = await client_for_tests.post(
            "/product_applications",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_application_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """404: Обновление несуществующего назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.patch(
            "/product_applications/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"code": "does_not_matter"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_application_no_data(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """400: Пустое тело запроса при обновлении назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture()

        response = await client_for_tests.patch(
            f"/product_applications/{app.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_application_duplicate_code(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """409: Изменение кода на уже существующий у другого назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="taken_code")
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="current_code")
        )

        response = await client_for_tests.patch(
            f"/product_applications/{app.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"code": "taken_code"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_reorder_application_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """404: Изменение порядка для несуществующего назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.patch(
            "/product_applications/999999/index",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_index": 0},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_application_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """404: Удаление несуществующего назначения."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.delete(
            "/product_applications/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_application_has_dependencies(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
    ):
        """400: Запрет удаления назначения, привязанного к товарам (rules_project.md пункт 5.1)."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        app = await create_product_application_fixture()
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=product.id, application_id=app.id)
        )

        response = await client_for_tests.delete(
            f"/product_applications/{app.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_translation_app_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """404: Добавление перевода к несуществующему назначению."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        response = await client_for_tests.post(
            "/product_applications/999999/translations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"locale": "rus", "name": "Тест"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_translation_already_exists(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """409: Перевод для указанной локали уже существует."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG)
        )

        response = await client_for_tests.post(
            f"/product_applications/{app.id}/translations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"locale": "eng", "name": "Duplicate Eng"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_translation_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """404: Обновление отсутствующего перевода."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG)
        )

        response = await client_for_tests.patch(
            f"/product_applications/{app.id}/translations/ger",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Ger Update"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_translation_no_data(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """400: Пустые данные при обновлении перевода."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG)
        )

        response = await client_for_tests.patch(
            f"/product_applications/{app.id}/translations/eng",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_translation_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """404: Удаление несуществующего перевода."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG)
        )

        response = await client_for_tests.delete(
            f"/product_applications/{app.id}/translations/rus",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_translation_last_one_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """400: Запрет удаления единственного оставшегося перевода (rules_project.md пункт 5.1)."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(locale=Language.ENG)
        )

        response = await client_for_tests.delete(
            f"/product_applications/{app.id}/translations/eng",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_product_applications_product_not_found(
        self,
        client_for_tests,
    ):
        """404: Запрос назначений несуществующего товара."""
        response = await client_for_tests.get("/product_applications/by-product/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_application_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """404: Привязка назначения к несуществующему товару."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture()

        response = await client_for_tests.post(
            "/product_applications/by-product/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"application_id": app.id},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_application_app_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
    ):
        """404: Привязка несуществующего назначения к товару."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()

        response = await client_for_tests.post(
            f"/product_applications/by-product/{product.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"application_id": 999999},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_application_already_assigned(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
    ):
        """409: Назначение уже привязано к товару."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        app = await create_product_application_fixture()
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=product.id, application_id=app.id)
        )

        response = await client_for_tests.post(
            f"/product_applications/by-product/{product.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"application_id": app.id},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_unassign_application_product_not_found(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_application_fixture,
    ):
        """404: Отвязка от несуществующего товара."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        app = await create_product_application_fixture()

        response = await client_for_tests.delete(
            f"/product_applications/by-product/999999/{app.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unassign_application_not_assigned(
        self,
        client_for_tests,
        create_user_fixture,
        create_product_fixture,
        create_product_application_fixture,
    ):
        """404: Назначение не было привязано к товару."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        product = await create_product_fixture()
        app = await create_product_application_fixture()

        response = await client_for_tests.delete(
            f"/product_applications/by-product/{product.id}/{app.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_inactive_application_by_id_anonymous_returns_404(
        self,
        client_for_tests,
        create_product_application_fixture,
    ):
        """Анонимный запрос неактивного назначения по ID -> 404."""
        app = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="inact_app_id", is_active=False)
        )
        response = await client_for_tests.get(f"/product_applications/{app.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_inactive_application_by_code_anonymous_returns_404(
        self,
        client_for_tests,
        create_product_application_fixture,
    ):
        """Анонимный запрос неактивного назначения по коду -> 404."""
        await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="inact_app_code", is_active=False)
        )
        response = await client_for_tests.get("/product_applications/by-code/inact_app_code")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_product_applications_filters_inactive_for_anonymous(
        self,
        client_for_tests,
        create_product_fixture,
        create_product_application_fixture,
        create_product_assigned_application_fixture,
    ):
        """Анонимный запрос назначений товара исключает неактивные назначения."""
        product = await create_product_fixture(CreateProductFixtureDTO(is_active=True))
        app_active = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="p_app_act", is_active=True)
        )
        app_inactive = await create_product_application_fixture(
            CreateProductApplicationFixtureDTO(code="p_app_inact", is_active=False)
        )
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=product.id, application_id=app_active.id)
        )
        await create_product_assigned_application_fixture(
            CreateProductAssignedApplicationFixtureDTO(product_id=product.id, application_id=app_inactive.id)
        )

        response = await client_for_tests.get(f"/product_applications/by-product/{product.id}")
        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert app_active.id in ids
        assert app_inactive.id not in ids
