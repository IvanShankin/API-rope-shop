from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.modules.base.exception import NoDataForUpdate
from src.modules.settings.models import Settings
from src.modules.settings.models_dto import SettingsResponseDTO, SettingsUpdateDTO, SettingsPublicResponseDTO
from src.modules.settings.repository import SettingsRepository


class SettingsService:

    def __init__(
        self,
        repo: SettingsRepository,
        session: AsyncSession,
        config: Optional[Config] = None,
    ):
        self.repo = repo
        self.session = session
        self.config = config or Config()

    def _get_default_settings_dict(self) -> dict:
        return self.config.default_site_settings.to_dict()

    async def _initialize_default_settings(self) -> Settings:
        """Инициализация настроек по умолчанию из конфигурации."""
        defaults = self._get_default_settings_dict()
        settings = await self.repo.add_settings(defaults)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def get_settings(self) -> SettingsResponseDTO:
        """Получение текущих настроек (автоинициализация при отсутствии)."""
        try:
            settings = await self.repo.get_settings()
        except Exception:
            # Сессия могла быть закрыта, если метод вызван в фоновой задаче после завершения запроса
            async with self.config.db_connection.session_local() as fallback_session:
                fallback_repo = SettingsRepository(session=fallback_session)
                settings = await fallback_repo.get_settings()
                if not settings:
                    settings = fallback_repo.add(self._get_default_settings_dict())
                    await fallback_session.commit()
                    await fallback_session.refresh(settings)
                return SettingsResponseDTO.model_validate(settings)

        if not settings:
            settings = await self._initialize_default_settings()
        return SettingsResponseDTO.model_validate(settings)

    async def get_public_settings(self) -> SettingsPublicResponseDTO:
        """Получение публичных настроек сайта (без чувствительных данных)."""
        full_settings = await self.get_settings()
        return SettingsPublicResponseDTO.model_validate(full_settings)

    async def get_settings_model(self) -> Settings:
        """Получение ORM-модели настроек (для внутреннего использования сервисами)."""
        settings = await self.repo.get_settings()
        if not settings:
            settings = await self._initialize_default_settings()
        return settings

    async def update_settings(self, data: SettingsUpdateDTO) -> SettingsResponseDTO:
        """Обновление настроек администратором."""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        settings = await self.repo.get_settings()
        if not settings:
            settings = await self._initialize_default_settings()

        await self.repo.update_settings(settings.id, update_data)
        await self.session.commit()
        await self.session.refresh(settings)
        return SettingsResponseDTO.model_validate(settings)
