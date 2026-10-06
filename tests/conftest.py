import pytest_asyncio

from fixturs import *
from src.modules.db_models import User
from src.modules.db_models import RefreshToken, SpliceMaterial, SplicePriceRule
from src.tools.creating_db import create_database

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete


@pytest_asyncio.fixture(scope='session', autouse=True)
async def start_test(config_fix, app_fastapi):
    if config_fix.env.mode != "TEST":
        raise RuntimeError("РСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РѕСЃРЅРѕРІРЅС‹Рµ .env РЅР°СЃС‚СЂРѕР№РєРё!")

    await create_database()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clearing_db(session_db: AsyncSession):
    """РћС‡РёС‰Р°РµС‚ Р±Р°Р·Сѓ Р±Р°РЅРЅС‹С…"""
    # СѓРґР°Р»СЏРµРј РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ РІ С‚Р°РєРѕРј РїРѕСЂСЏРґРєРµ
    await session_db.execute(delete(RefreshToken))
    await session_db.execute(delete(User))
    await session_db.execute(delete(SplicePriceRule))
    await session_db.execute(delete(SpliceMaterial))
    await session_db.commit()

