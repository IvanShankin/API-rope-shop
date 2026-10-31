import pytest

from src.modules.notifications.models_dto import TestNotificationResponseDTO
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_admin_can_test_telegram_notification(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор успешно тестирует отправку сообщения в Telegram."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client_for_tests.post(
            "/notifications/test/telegram",
            headers=headers,
        )
        assert response.status_code == 200
        dto = TestNotificationResponseDTO.model_validate(response.json())
        assert dto.success is True
        assert dto.target is not None
        assert "успешно" in dto.message.lower()

    @pytest.mark.asyncio
    async def test_admin_can_test_telegram_with_custom_chat_id(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор тестирует отправку в Telegram с переопределением chat_id в теле запроса."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client_for_tests.post(
            "/notifications/test/telegram",
            json={"chat_id": "-100999888777"},
            headers=headers,
        )
        assert response.status_code == 200
        dto = TestNotificationResponseDTO.model_validate(response.json())
        assert dto.success is True
        assert dto.target == "-100999888777"

    @pytest.mark.asyncio
    async def test_admin_can_test_email_notification(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор успешно тестирует отправку email."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client_for_tests.post(
            "/notifications/test/email",
            headers=headers,
        )
        assert response.status_code == 200
        dto = TestNotificationResponseDTO.model_validate(response.json())
        assert dto.success is True
        assert dto.target is not None
        assert "успешно" in dto.message.lower()

    @pytest.mark.asyncio
    async def test_admin_can_test_email_with_custom_to_email(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор тестирует отправку email с переопределением to_email."""
        _, admin_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.ADMIN)
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await client_for_tests.post(
            "/notifications/test/email",
            json={"to_email": "custom.admin@example.com"},
            headers=headers,
        )
        assert response.status_code == 200
        dto = TestNotificationResponseDTO.model_validate(response.json())
        assert dto.success is True
        assert dto.target == "custom.admin@example.com"


class TestsForPermission:

    @pytest.mark.asyncio
    async def test_regular_user_cannot_test_telegram(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Обычный пользователь (не админ) получает 403 при попытке тестирования Telegram."""
        _, user_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        headers = {"Authorization": f"Bearer {user_token}"}

        response = await client_for_tests.post(
            "/notifications/test/telegram",
            headers=headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthorized_user_cannot_test_telegram(
        self,
        client_for_tests,
    ):
        """Неавторизованный пользователь получает 401."""
        response = await client_for_tests.post("/notifications/test/telegram")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_regular_user_cannot_test_email(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Обычный пользователь получает 403 при попытке тестирования Email."""
        _, user_token = await create_user_fixture(
            CreateUserFixtureDTO(role=UserRole.USER)
        )
        headers = {"Authorization": f"Bearer {user_token}"}

        response = await client_for_tests.post(
            "/notifications/test/email",
            headers=headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthorized_user_cannot_test_email(
        self,
        client_for_tests,
    ):
        """Неавторизованный пользователь получает 401 при попытке тестирования Email."""
        response = await client_for_tests.post("/notifications/test/email")
        assert response.status_code == 401
