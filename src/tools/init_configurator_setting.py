import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.modules.configurator_setting.models import ConfiguratorSetting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("init_configurator_setting")


async def init_configurator_setting(
    session: Optional[AsyncSession] = None,
    config: Optional[Config] = None,
) -> ConfiguratorSetting:
    """
    Создаёт единственную запись в ConfiguratorSetting при её отсутствии,
    используя настройки по умолчанию из модели ConfiguratorSetting.

    :param session: Опциональная асинхронная сессия SQLAlchemy.
    :param config: Опциональный объект конфигурации Config.
    :return: Объект ConfiguratorSetting (созданный или уже существующий).
    """
    if session is not None:
        return await _create_setting_if_not_exists(session)

    conf = config or Config()
    async_session_factory = conf.db_connection.session_local
    async with async_session_factory() as local_session:
        return await _create_setting_if_not_exists(local_session)


async def _create_setting_if_not_exists(session: AsyncSession) -> ConfiguratorSetting:
    """
    Проверяет наличие записи ConfiguratorSetting и создаёт её с дефолтными значениями,
    если таблица пуста.
    """
    stmt = select(ConfiguratorSetting).limit(1)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting is None:
        logger.info("ConfiguratorSetting record not found. Creating with default model values...")
        setting = ConfiguratorSetting()
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
        logger.info(
            f"ConfiguratorSetting created successfully (id={setting.id}, "
            f"min_length_m={setting.min_length_m}, max_length_m={setting.max_length_m}, "
            f"currency={setting.currency.value})"
        )
    else:
        logger.info(f"ConfiguratorSetting already exists (id={setting.id}). Skipping creation.")

    return setting


def main() -> None:
    """Точка входа при вызове скрипта из консоли."""
    asyncio.run(init_configurator_setting())


if __name__ == "__main__":
    main()
