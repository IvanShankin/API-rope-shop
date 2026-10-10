import pytest_asyncio

from fixturs import *
from src.modules.db_models import User
from src.modules.db_models import (
    RefreshToken,
    SpliceMaterial,
    SplicePriceRule,
    SpliceType,
    SpliceTypeTranslation,
    Color,
    ColorTranslation,
    RopeProductColor,
    RopeAllowedSplice,
    RopeVariant,
    RopeProduct,
    Product,
    MaterialGroup,
    MaterialGroupTranslation,
    Material,
    MaterialTranslation,
    QuoteRequest,
    QuoteRopeItem,
    QuoteServiceItem,
)
from src.tools.creating_db import create_database

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete


@pytest_asyncio.fixture(scope='session', autouse=True)
async def start_test(config_fix, app_fastapi):
    if config_fix.env.mode != "TEST":
        raise RuntimeError("Используется основные .env настройки!")

    await create_database()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clearing_db(session_db: AsyncSession):
    """Очищает базу данных"""
    # Удаляем обязательно в таком порядке
    await session_db.execute(delete(QuoteRopeItem))
    await session_db.execute(delete(QuoteServiceItem))
    await session_db.execute(delete(QuoteRequest))
    await session_db.execute(delete(RopeAllowedSplice))
    await session_db.execute(delete(RopeProductColor))
    await session_db.execute(delete(RopeVariant))
    await session_db.execute(delete(RopeProduct))
    await session_db.execute(delete(Product))
    await session_db.execute(delete(MaterialTranslation))
    await session_db.execute(delete(Material))
    await session_db.execute(delete(MaterialGroupTranslation))
    await session_db.execute(delete(MaterialGroup))
    await session_db.execute(delete(RefreshToken))
    await session_db.execute(delete(User))
    await session_db.execute(delete(SplicePriceRule))
    await session_db.execute(delete(SpliceMaterial))
    await session_db.execute(delete(SpliceTypeTranslation))
    await session_db.execute(delete(SpliceType))
    await session_db.execute(delete(ColorTranslation))
    await session_db.execute(delete(Color))
    await session_db.commit()
