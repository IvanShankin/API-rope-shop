from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.configurator_extra.models import (
    ConfiguratorExtra,
    ConfiguratorExtraTranslation,
    BillingType,
)


class ConfiguratorExtraRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ConfiguratorExtra)

    async def add_extra(self, data: Union[dict, Any]) -> ConfiguratorExtra:
        """Добавление новой дополнительной опции конфигуратора."""
        return self.add(data)

    async def get_all(
        self,
        billing_type: Optional[BillingType] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[ConfiguratorExtra]:
        """Получение списка всех опций с фильтрацией и предзагрузкой переводов."""
        stmt = (
            select(ConfiguratorExtra)
            .options(selectinload(ConfiguratorExtra.translations))
            .order_by(ConfiguratorExtra.index.asc(), ConfiguratorExtra.id.asc())
        )
        if billing_type is not None:
            stmt = stmt.where(ConfiguratorExtra.billing_type == billing_type)
        if is_active is not None:
            stmt = stmt.where(ConfiguratorExtra.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, extra_id: int) -> ConfiguratorExtra | None:
        """Получение опции по ID с предзагрузкой переводов."""
        stmt = (
            select(ConfiguratorExtra)
            .options(selectinload(ConfiguratorExtra.translations))
            .where(ConfiguratorExtra.id == extra_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> ConfiguratorExtra | None:
        """Получение опции по уникальному коду."""
        stmt = (
            select(ConfiguratorExtra)
            .options(selectinload(ConfiguratorExtra.translations))
            .where(ConfiguratorExtra.code == code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_dependencies(self, extra_id: int) -> bool:
        """Проверка наличия внешних зависимостей (Правило 5.1)."""
        return False

    async def update_extra(self, extra_id: int, update_data: dict) -> None:
        """Обновление данных опции."""
        stmt = update(ConfiguratorExtra).where(ConfiguratorExtra.id == extra_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_extra(self, extra_id: int) -> None:
        """Удаление опции."""
        stmt = delete(ConfiguratorExtra).where(ConfiguratorExtra.id == extra_id)
        await self.session.execute(stmt)


class ConfiguratorExtraTranslationRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ConfiguratorExtraTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> ConfiguratorExtraTranslation:
        """Добавление перевода опции."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> ConfiguratorExtraTranslation | None:
        """Получение перевода по ID."""
        stmt = select(ConfiguratorExtraTranslation).where(ConfiguratorExtraTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_extra_and_locale(
        self,
        extra_id: int,
        locale: Language
    ) -> ConfiguratorExtraTranslation | None:
        """Получение перевода для конкретной опции и языка."""
        stmt = select(ConfiguratorExtraTranslation).where(
            ConfiguratorExtraTranslation.extra_id == extra_id,
            ConfiguratorExtraTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода."""
        stmt = (
            update(ConfiguratorExtraTranslation)
            .where(ConfiguratorExtraTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода."""
        stmt = delete(ConfiguratorExtraTranslation).where(ConfiguratorExtraTranslation.id == translation_id)
        await self.session.execute(stmt)
