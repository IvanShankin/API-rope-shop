import asyncio
import pytest
from passlib.context import CryptContext
from sqlalchemy import select

from src.modules.settings.models import Settings
from src.modules.configurator_setting.models import ConfiguratorSetting
from src.modules.contact_requests.models import ContactRequest
from src.modules.users.models import User, UserRole
from src.tools.init_settings import init_settings
from src.tools.init_configurator_setting import init_configurator_setting
from src.tools.init_contact_request import init_contact_request
from src.tools.init_admin import init_admin


@pytest.mark.asyncio
async def test_concurrent_init_settings_creates_single_row(session_db, not_open_session_db, config_fix):
    """Одновременный запуск init_settings из нескольких воркеров создаёт ровно одну запись."""
    async def worker():
        async with not_open_session_db() as s:
            return await init_settings(session=s, config=config_fix)

    tasks = [worker() for _ in range(4)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    for item in results:
        assert item.company_name == config_fix.default_site_settings.company_name

    rows = (await session_db.execute(select(Settings))).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_concurrent_init_configurator_setting_creates_single_row(session_db, not_open_session_db, config_fix):
    """Одновременный запуск init_configurator_setting создаёт ровно одну запись."""
    async def worker():
        async with not_open_session_db() as s:
            return await init_configurator_setting(session=s, config=config_fix)

    tasks = [worker() for _ in range(4)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    rows = (await session_db.execute(select(ConfiguratorSetting))).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_concurrent_init_contact_request_creates_single_row(session_db, not_open_session_db, config_fix):
    """Одновременный запуск init_contact_request создаёт ровно одну запись."""
    async def worker():
        async with not_open_session_db() as s:
            return await init_contact_request(session=s, config=config_fix)

    tasks = [worker() for _ in range(4)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    rows = (await session_db.execute(select(ContactRequest))).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_concurrent_init_admin_creates_single_admin(session_db, not_open_session_db, config_fix):
    """Одновременный запуск init_admin создаёт ровно одного администратора."""
    cr_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def worker():
        async with not_open_session_db() as s:
            return await init_admin(session=s, config=config_fix, cr_context=cr_context)

    tasks = [worker() for _ in range(4)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    rows = (await session_db.execute(select(User).where(User.role == UserRole.ADMIN))).scalars().all()
    assert len(rows) == 1
