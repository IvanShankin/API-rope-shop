from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.locks import acquire_advisory_lock, LOCK_ID_INIT_CONFIGURATOR_SETTING
from src.modules.base.exception import NoDataForUpdate
from src.modules.configurator_setting.models import ConfiguratorSetting, Currency
from src.modules.configurator_setting.models_dto import (
    ConfiguratorSettingResponseDTO,
    ConfiguratorSettingUpdateDTO,
)
from src.modules.configurator_setting.repository import ConfiguratorSettingRepository
from src.modules.configurator_setting.exception import ConfiguratorSettingValidationError


DEFAULT_SETTINGS = {
    "min_length_m": 1.0,
    "max_length_m": 200.0,
    "splice_allowance_until_mm": 12.0,
    "splice_allowance_until_m": 0.6,
    "splice_allowance_over_m": 1.0,
    "urgent_surcharge_per_splice": 10.0,
    "urgent_max_splices": 10,
    "standard_turnaround_hours": 72,
    "urgent_turnaround_hours": 24,
    "currency": Currency.EUR,
    "vat_rate": 0.0,
    "vat_note": "inkl. MwSt.",
}


class ConfiguratorSettingService:
    def __init__(
        self,
        repo: ConfiguratorSettingRepository,
        session: AsyncSession,
    ):
        self.repo = repo
        self.session = session

    async def get_settings(self) -> ConfiguratorSettingResponseDTO:
        """Получение текущих настроек конфигуратора (с автоинициализацией по умолчанию при первом вызове)."""
        settings = await self.repo.get_settings()
        if not settings:
            settings = await self._initialize_default_settings()

        return ConfiguratorSettingResponseDTO.model_validate(settings)

    async def update_settings(
        self,
        data: ConfiguratorSettingUpdateDTO,
    ) -> ConfiguratorSettingResponseDTO:
        """Обновление настроек конфигуратора администратором."""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        settings = await self.repo.get_settings()
        if not settings:
            settings = await self._initialize_default_settings()

        # Валидация диапазонов длины каната
        effective_min = update_data.get("min_length_m", float(settings.min_length_m))
        effective_max = update_data.get("max_length_m", float(settings.max_length_m))
        if effective_min > effective_max:
            raise ConfiguratorSettingValidationError(
                "min_length_m cannot be greater than max_length_m."
            )

        await self.repo.update_settings(settings.id, update_data)
        await self.session.commit()

        updated = await self.repo.get_settings()
        return ConfiguratorSettingResponseDTO.model_validate(updated)

    async def _initialize_default_settings(self) -> ConfiguratorSetting:
        """Создание начальной строки настроек по умолчанию."""
        await acquire_advisory_lock(self.session, LOCK_ID_INIT_CONFIGURATOR_SETTING)
        existing = await self.repo.get_settings()
        if existing:
            return existing
        setting = ConfiguratorSetting(**DEFAULT_SETTINGS)
        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting
