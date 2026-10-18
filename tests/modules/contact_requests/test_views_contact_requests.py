import pytest
from sqlalchemy import select

from src.modules.contact_requests.models import ContactRequest
from src.modules.contact_requests.models_dto import (
    ContactRequestResponseDTO,
    ContactRequestUpdateDTO,
)
from src.modules.users.models import UserRole
from src.tools.init_contact_request import init_contact_request
from tests.modules.contact_requests.fixtures.models_dto import (
    CreateContactRequestFixtureDTO,
)
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_contact_request_public_auto_init(
        self,
        client_for_tests,
    ):
        """
        Публичное получение контактной формы.
        Если таблица пуста, сервис автоматически создает запись со значениями по умолчанию.
        """
        response = await client_for_tests.get("/contact_requests")
        assert response.status_code == 200

        data = ContactRequestResponseDTO.model_validate(response.json())
        assert data.name == "General Contact"
        assert data.email == "info@ropeshop.com"
        assert data.phone is not None

    @pytest.mark.asyncio
    async def test_get_existing_contact_request_public(
        self,
        client_for_tests,
        create_contact_request_fixture,
    ):
        """Публичное получение существующей контактной формы."""
        contact = await create_contact_request_fixture(
            CreateContactRequestFixtureDTO(
                name="Rope Shop HQ",
                email="hq@ropeshop.com",
                phone="+49 30 123456",
                message="Berlin Office",
            )
        )

        response = await client_for_tests.get("/contact_requests")
        assert response.status_code == 200

        data = ContactRequestResponseDTO.model_validate(response.json())
        assert data.id == contact.id
        assert data.name == "Rope Shop HQ"
        assert data.email == "hq@ropeshop.com"
        assert data.phone == "+49 30 123456"

    @pytest.mark.asyncio
    async def test_get_contact_request_by_id_public(
        self,
        client_for_tests,
        create_contact_request_fixture,
    ):
        """Получение контактной формы по ID (публичный доступ)."""
        contact = await create_contact_request_fixture(
            CreateContactRequestFixtureDTO(name="Contact by ID")
        )

        response = await client_for_tests.get(f"/contact_requests/{contact.id}")
        assert response.status_code == 200

        data = ContactRequestResponseDTO.model_validate(response.json())
        assert data.id == contact.id
        assert data.name == "Contact by ID"

    @pytest.mark.asyncio
    async def test_update_contact_request_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_contact_request_fixture,
        session_db,
    ):
        """Обновление контактной формы администратором."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        contact = await create_contact_request_fixture(
            CreateContactRequestFixtureDTO(
                name="Initial Name",
                email="old@ropeshop.com",
            )
        )

        update_dto = ContactRequestUpdateDTO(
            name="Updated Support Name",
            email="support@ropeshop.com",
            phone="+1 800 555 ROPE",
            message="New updated office hours and message",
        )

        response = await client_for_tests.patch(
            "/contact_requests",
            headers=headers,
            json=update_dto.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        data = ContactRequestResponseDTO.model_validate(response.json())
        assert data.id == contact.id
        assert data.name == "Updated Support Name"
        assert data.email == "support@ropeshop.com"
        assert data.phone == "+1 800 555 ROPE"

        # Проверка сохранения в БД
        db_contact = (
            await session_db.execute(
                select(ContactRequest).where(ContactRequest.id == contact.id)
            )
        ).scalar_one()
        assert db_contact.name == "Updated Support Name"
        assert db_contact.email == "support@ropeshop.com"

    @pytest.mark.asyncio
    async def test_update_contact_request_by_id_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_contact_request_fixture,
    ):
        """Обновление контактной формы по ID администратором."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        contact = await create_contact_request_fixture()

        update_dto = ContactRequestUpdateDTO(phone="+44 20 7946 0991")

        response = await client_for_tests.patch(
            f"/contact_requests/{contact.id}",
            headers=headers,
            json=update_dto.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        data = ContactRequestResponseDTO.model_validate(response.json())
        assert data.id == contact.id
        assert data.phone == "+44 20 7946 0991"

    @pytest.mark.asyncio
    async def test_init_contact_request_script(
        self,
        session_db,
    ):
        """Проверка работы скрипта init_contact_request (создание при отсутствии, пропуск при наличии)."""
        # 1. Запуск на пустой таблице -> создает запись
        first_contact = await init_contact_request(session=session_db)
        assert first_contact is not None
        assert first_contact.id is not None
        assert first_contact.name == "General Contact"

        # 2. Повторный запуск -> находит существующую и возвращает ее же
        second_contact = await init_contact_request(session=session_db)
        assert second_contact.id == first_contact.id
        assert second_contact.email == first_contact.email


class TestsForFailed:

    @pytest.mark.asyncio
    async def test_get_nonexistent_contact_request_by_id_returns_404(
        self,
        client_for_tests,
    ):
        """Запрос несуществующего ID контактной формы возвращает 404."""
        response = await client_for_tests.get("/contact_requests/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_contact_request_unauthorized_returns_401(
        self,
        client_for_tests,
    ):
        """Попытка изменения контактной формы без авторизации возвращает 401."""
        response = await client_for_tests.patch(
            "/contact_requests",
            json={"name": "Hacker Name"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_contact_request_regular_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка изменения контактной формы пользователем с ролью USER возвращает 403."""
        _, user_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        headers = {"Authorization": f"Bearer {user_token}"}

        response = await client_for_tests.patch(
            "/contact_requests",
            headers=headers,
            json={"name": "User Attempt"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_contact_request_by_id_returns_404(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка обновления несуществующего ID возвращает 404."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client_for_tests.patch(
            "/contact_requests/99999",
            headers=headers,
            json={"name": "No One"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_contact_request_no_data_returns_400(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка обновления без передачи полей возвращает 400 Bad Request."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client_for_tests.patch(
            "/contact_requests",
            headers=headers,
            json={},
        )
        assert response.status_code == 400
