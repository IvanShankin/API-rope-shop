import pytest

from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from src.modules.settings.models_dto import SettingsResponseDTO, SettingsUpdateDTO


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
