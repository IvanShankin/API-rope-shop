import pytest

from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.configurator_setting.fixtures.models_dto import (
    CreateConfiguratorSettingFixtureDTO,
)
from src.modules.configurator_setting.models import Currency
from src.modules.configurator_setting.models_dto import (
    ConfiguratorSettingResponseDTO,
    ConfiguratorSettingUpdateDTO,
)


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_get_settings_public_auto_initialized(
        self,
        client_for_tests,
    ):
        """Любой пользователь может получить настройки конфигуратора (public), они инициализируются дефолтными значениями при отсутствии."""
        response = await client_for_tests.get("/configurator_settings")
        assert response.status_code == 200

        dto = ConfiguratorSettingResponseDTO.model_validate(response.json())
        assert dto.min_length_m == 1.0
        assert dto.max_length_m == 200.0
        assert dto.currency == Currency.EUR
        assert dto.urgent_surcharge_per_splice == 10.0

    @pytest.mark.asyncio
    async def test_get_settings_existing(
        self,
        client_for_tests,
        create_configurator_setting_fixture,
    ):
        """Получение существующего объекта настроек конфигуратора."""
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(min_length_m=2.0, max_length_m=150.0)
        )

        response = await client_for_tests.get("/configurator_settings")
        assert response.status_code == 200

        dto = ConfiguratorSettingResponseDTO.model_validate(response.json())
        assert dto.min_length_m == 2.0
        assert dto.max_length_m == 150.0

    @pytest.mark.asyncio
    async def test_update_settings_admin(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_setting_fixture,
    ):
        """Администратор успешно обновляет единственный объект настроек конфигуратора."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(min_length_m=1.0, max_length_m=200.0)
        )

        payload = ConfiguratorSettingUpdateDTO(
            min_length_m=3.0,
            max_length_m=250.0,
            urgent_surcharge_per_splice=15.0,
            vat_rate=19.0,
            vat_note="MwSt 19%",
        )

        response = await client_for_tests.patch(
            "/configurator_settings",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(exclude_unset=True),
        )
        assert response.status_code == 200

        dto = ConfiguratorSettingResponseDTO.model_validate(response.json())
        assert dto.min_length_m == 3.0
        assert dto.max_length_m == 250.0
        assert dto.urgent_surcharge_per_splice == 15.0
        assert dto.vat_rate == 19.0
        assert dto.vat_note == "MwSt 19%"


class TestsForFailures:

    @pytest.mark.asyncio
    async def test_update_settings_unauthorized(
        self,
        client_for_tests,
    ):
        """Попытка изменения настроек без токена -> 401."""
        response = await client_for_tests.patch(
            "/configurator_settings",
            json={"min_length_m": 5.0},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_settings_forbidden(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        """Попытка изменения настроек обычным пользователем -> 403."""
        user, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.USER))\

        response = await client_for_tests.patch(
            "/configurator_settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"min_length_m": 5.0},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_settings_no_data(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_setting_fixture,
    ):
        """Пустой запрос на изменение настроек -> 400 Bad Request."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        await create_configurator_setting_fixture()

        response = await client_for_tests.patch(
            "/configurator_settings",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_settings_invalid_range(
        self,
        client_for_tests,
        create_user_fixture,
        create_configurator_setting_fixture,
    ):
        """Попытка установки min_length_m больше max_length_m -> 400 Bad Request."""
        admin, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.ADMIN))
        await create_configurator_setting_fixture(
            CreateConfiguratorSettingFixtureDTO(min_length_m=1.0, max_length_m=50.0)
        )

        response = await client_for_tests.patch(
            "/configurator_settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"min_length_m": 100.0, "max_length_m": 50.0},
        )
        assert response.status_code == 400
