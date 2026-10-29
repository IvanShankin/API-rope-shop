import pytest

from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from src.modules.settings.models_dto import (
    SettingsResponseDTO,
    SettingsUpdateDTO,
    SettingsPublicResponseDTO,
)


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_settings_admin_success(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор успешно получает системные настройки."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        response = await client_for_tests.get(
            "/settings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        dto = SettingsResponseDTO.model_validate(response.json())
        assert dto.id is not None
        assert dto.company_name == "Rope Shop"
        assert dto.telegram_notifications_enabled is True

    @pytest.mark.asyncio
    async def test_get_settings_public_unauthorized_success(
        self,
        client_for_tests,
    ):
        """Публичный пользователь (без авторизации) успешно получает открытые настройки."""
        response = await client_for_tests.get("/settings/public")
        assert response.status_code == 200

        data = response.json()
        dto = SettingsPublicResponseDTO.model_validate(data)
        assert dto.company_name == "Rope Shop"

        # Проверяем, что чувствительные и системные поля не отдаются публично
        assert "telegram_chat_id" not in data
        assert "telegram_notifications_enabled" not in data
        assert "email_notifications_enabled" not in data
        assert "manager_notification_email" not in data
        assert "manager_email_notifications_enabled" not in data
        assert "id" not in data
        assert "created_at" not in data
        assert "updated_at" not in data

    @pytest.mark.asyncio
    async def test_get_settings_public_authorized_user_success(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Авторизованный пользователь с ролью USER также успешно получает открытые настройки."""
        user, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))

        response = await client_for_tests.get(
            "/settings/public",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        dto = SettingsPublicResponseDTO.model_validate(response.json())
        assert dto.company_name == "Rope Shop"

    @pytest.mark.asyncio
    async def test_get_settings_public_reflects_admin_updates(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Публичный эндпоинт отдает обновленные администратором публичные данные."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        payload = SettingsUpdateDTO(
            company_name="Updated Public Rope Store",
            contact_email="public@ropestore.de",
            contact_phone="+49 987 654321",
            site_url="https://ropestore.de",
            telegram_chat_id="-10099999999",
        )

        patch_response = await client_for_tests.patch(
            "/settings",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(exclude_unset=True),
        )
        assert patch_response.status_code == 200

        # Запрашиваем без токена
        public_response = await client_for_tests.get("/settings/public")
        assert public_response.status_code == 200
        data = public_response.json()
        dto = SettingsPublicResponseDTO.model_validate(data)

        assert dto.company_name == "Updated Public Rope Store"
        assert dto.contact_email == "public@ropestore.de"
        assert dto.contact_phone == "+49 987 654321"
        assert dto.site_url == "https://ropestore.de"
        assert "telegram_chat_id" not in data

    @pytest.mark.asyncio
    async def test_patch_settings_admin_success(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор успешно обновляет настройки (включая telegram_chat_id)."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        payload = SettingsUpdateDTO(
            telegram_chat_id="-1001122334455",
            telegram_notifications_enabled=True,
            company_name="Updated Rope Shop",
            contact_phone="+49 123 456789",
        )

        response = await client_for_tests.patch(
            "/settings",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200
        dto = SettingsResponseDTO.model_validate(response.json())
        assert dto.telegram_chat_id == "-1001122334455"
        assert dto.company_name == "Updated Rope Shop"
        assert dto.contact_phone == "+49 123 456789"

    @pytest.mark.asyncio
    async def test_put_settings_admin_success(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Администратор обновляет настройки через PUT."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        payload = SettingsUpdateDTO(
            telegram_chat_id="-1009988776655",
            email_notifications_enabled=False,
        )

        response = await client_for_tests.put(
            "/settings",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200
        dto = SettingsResponseDTO.model_validate(response.json())
        assert dto.telegram_chat_id == "-1009988776655"
        assert dto.email_notifications_enabled is False


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_get_settings_unauthorized_returns_401(
        self,
        client_for_tests,
    ):
        """Неавторизованный запрос настроек -> 401."""
        response = await client_for_tests.get("/settings")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_settings_forbidden_for_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Запрос настроек обычным пользователем (не админом) -> 403."""
        user, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))

        response = await client_for_tests.get(
            "/settings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_patch_settings_unauthorized_returns_401(
        self,
        client_for_tests,
    ):
        """Попытка изменения без токена -> 401."""
        response = await client_for_tests.patch(
            "/settings",
            json={"company_name": "Hacked"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_patch_settings_forbidden_for_user_returns_403(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка изменения обычным пользователем -> 403."""
        user, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))

        response = await client_for_tests.patch(
            "/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"company_name": "New Shop"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_patch_settings_no_data_returns_400(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Пустое тело обновления -> 400 Bad Request."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))

        response = await client_for_tests.patch(
            "/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 400
