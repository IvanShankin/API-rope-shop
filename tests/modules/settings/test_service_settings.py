import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NoDataForUpdate
from src.modules.settings.models_dto import SettingsUpdateDTO
from src.modules.settings.repository import SettingsRepository
from src.modules.settings.service import SettingsService


@pytest.mark.asyncio
async def test_get_settings_auto_initializes(session_db: AsyncSession):
    repo = SettingsRepository(session=session_db)
    service = SettingsService(repo=repo, session=session_db)

    settings = await service.get_settings()
    assert settings.id is not None
    assert settings.company_name == "Rope Shop"
    assert settings.telegram_notifications_enabled is True
    assert settings.email_notifications_enabled is True


@pytest.mark.asyncio
async def test_update_settings_success(session_db: AsyncSession):
    repo = SettingsRepository(session=session_db)
    service = SettingsService(repo=repo, session=session_db)

    update_dto = SettingsUpdateDTO(
        telegram_chat_id="-100987654321",
        telegram_notifications_enabled=True,
        company_name="Alpine Rope Store",
        contact_email="support@alpineropestore.com",
    )

    updated = await service.update_settings(update_dto)
    assert updated.telegram_chat_id == "-100987654321"
    assert updated.company_name == "Alpine Rope Store"
    assert updated.contact_email == "support@alpineropestore.com"


@pytest.mark.asyncio
async def test_update_settings_no_data_raises(session_db: AsyncSession):
    repo = SettingsRepository(session=session_db)
    service = SettingsService(repo=repo, session=session_db)

    with pytest.raises(NoDataForUpdate):
        await service.update_settings(SettingsUpdateDTO())
