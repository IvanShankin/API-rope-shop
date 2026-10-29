from typing import Union, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.configurator_setting.models import ConfiguratorSetting


class ConfiguratorSettingRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ConfiguratorSetting)

    async def get_settings(self) -> ConfiguratorSetting | None:
        """Получение единственной записи настроек конфигуратора."""
        stmt = select(ConfiguratorSetting).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_settings(self, data: Union[dict, Any]) -> ConfiguratorSetting:
        """Создание записи настроек."""
        return self.add(data)

    async def update_settings(self, settings_id: int, update_data: dict) -> None:
        """Обновление записи настроек."""
        stmt = (
            update(ConfiguratorSetting)
            .where(ConfiguratorSetting.id == settings_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
