from typing import Any, Union
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.settings.models import Settings


class SettingsRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Settings)

    async def get_settings(self) -> Settings | None:
        """Получение единственной записи настроек."""
        stmt = select(Settings).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_settings(self, data: Union[dict, Any]) -> Settings:
        """Создание записи настроек."""
        return self.add(data)

    async def update_settings(self, settings_id: int, update_data: dict) -> None:
        """Обновление записи настроек."""
        stmt = (
            update(Settings)
            .where(Settings.id == settings_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
