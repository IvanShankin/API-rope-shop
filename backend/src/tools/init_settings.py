import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.database.locks import acquire_advisory_lock, LOCK_ID_INIT_SETTINGS
from src.modules.settings.models import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("init_settings")


async def init_settings(
    session: Optional[AsyncSession] = None,
    config: Optional[Config] = None,
) -> Settings:
    """
    Создаёт начальную запись в site_settings при её отсутствии.
    Если запись уже есть, создание пропускается.

    :param session: Опциональная асинхронная сессия SQLAlchemy.
    :param config: Опциональный объект конфигурации Config.
    :return: Объект Settings (созданный или уже существующий).
    """
    conf = config or Config()
    default_data = conf.default_site_settings.to_dict()

    if session is not None:
        return await _create_settings_if_not_exists(session, default_data)

    async_session_factory = conf.db_connection.session_local
    async with async_session_factory() as local_session:
        return await _create_settings_if_not_exists(local_session, default_data)


async def _create_settings_if_not_exists(session: AsyncSession, default_data: dict) -> Settings:
    # Захватываем рекомендательную блокировку для предотвращения гонок между несколькими воркерами
    await acquire_advisory_lock(session, LOCK_ID_INIT_SETTINGS)

    stmt = select(Settings).limit(1)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting is None:
        logger.info("Site settings not found. Creating default settings from config...")
        setting = Settings(**default_data)
        try:
            session.add(setting)
            await session.commit()
            await session.refresh(setting)
            logger.info(
                f"Site settings created successfully (id={setting.id}, "
                f"company_name='{setting.company_name}', telegram_chat_id='{setting.telegram_chat_id}')."
            )
        except IntegrityError:
            await session.rollback()
            logger.info("Site settings created concurrently by another process.")
            res = await session.execute(select(Settings).limit(1))
            setting = res.scalar_one_or_none()
    else:
        logger.info(f"Site settings already exist (id={setting.id}). Skipping creation.")
        await session.commit()

    return setting


def main() -> None:
    """Точка входа при вызове скрипта из консоли."""
    asyncio.run(init_settings())


if __name__ == "__main__":
    main()
