from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.configurator_extra.models import BillingType
from src.modules.configurator_extra.repository import (
    ConfiguratorExtraRepository,
    ConfiguratorExtraTranslationRepository,
)
from src.modules.configurator_extra.models_dto import (
    ConfiguratorExtraBase,
    ConfiguratorExtraCreate,
    ConfiguratorExtraUpdate,
    ConfiguratorExtraUpdateIndexDTO,
    ConfiguratorExtraResponseDTO,
    ConfiguratorExtraLocalizedResponseDTO,
    ConfiguratorExtraTranslationCreate,
    ConfiguratorExtraTranslationInsert,
    ConfiguratorExtraTranslationUpdate,
    ConfiguratorExtraTranslationResponseDTO,
)
from src.modules.configurator_extra.exception import (
    ConfiguratorExtraNotFound,
    ConfiguratorExtraAlreadyExists,
    ConfiguratorExtraTranslationNotFound,
    ConfiguratorExtraTranslationAlreadyExists,
    ConfiguratorExtraTranslationDeleteError,
    ConfiguratorExtraHasDependencies,
)


class ConfiguratorExtraService:
    def __init__(
        self,
        extra_repo: ConfiguratorExtraRepository,
        translation_repo: ConfiguratorExtraTranslationRepository,
        session: AsyncSession,
    ):
        self.extra_repo = extra_repo
        self.translation_repo = translation_repo
        self.session = session

    async def create_extra(
        self,
        data: ConfiguratorExtraCreate,
    ) -> ConfiguratorExtraResponseDTO:
        """Создание новой дополнительной опции конфигуратора с обязательными переводами."""
        if not data.translations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one translation is required when creating a ConfiguratorExtra.",
            )

        existing = await self.extra_repo.get_by_code(data.code)
        if existing:
            raise ConfiguratorExtraAlreadyExists(
                f"ConfiguratorExtra with code '{data.code}' already exists."
            )

        locales = [t.locale for t in data.translations]
        if len(locales) != len(set(locales)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate locales found in translations.",
            )

        if data.index is None:
            max_index = await self.extra_repo.get_max_index()
            target_index = max_index + 1
        else:
            target_index = data.index
            await self.extra_repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = ConfiguratorExtraBase(
            code=data.code,
            price=data.price,
            currency=data.currency,
            billing_type=data.billing_type,
            index=target_index,
            is_active=data.is_active,
        )
        new_extra = await self.extra_repo.add_extra(base_dto)
        await self.session.flush()

        for trans_data in data.translations:
            insert_dto = ConfiguratorExtraTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                description=trans_data.description,
                extra_id=new_extra.id,
            )
            await self.translation_repo.add_translation(insert_dto)

        await self.session.commit()
        created_extra = await self.extra_repo.get_by_id(new_extra.id)
        return ConfiguratorExtraResponseDTO.model_validate(created_extra)

    async def get_all_extras(
        self,
        locale: Optional[Language] = None,
        is_active: Optional[bool] = None,
        billing_type: Optional[BillingType] = None,
    ) -> List[ConfiguratorExtraLocalizedResponseDTO]:
        """Получение списка всех опций с локализацией по указанному языку."""
        extras = await self.extra_repo.get_all(
            billing_type=billing_type,
            is_active=is_active,
        )
        return [self._to_localized_dto(e, locale) for e in extras]

    async def get_extra_by_id(
        self,
        extra_id: int,
    ) -> ConfiguratorExtraResponseDTO:
        """Получение опции по ID со всеми переводами."""
        extra = await self.extra_repo.get_by_id(extra_id)
        if not extra:
            raise ConfiguratorExtraNotFound(
                f"ConfiguratorExtra with id {extra_id} not found."
            )
        return ConfiguratorExtraResponseDTO.model_validate(extra)

    async def update_extra(
        self,
        extra_id: int,
        data: ConfiguratorExtraUpdate,
    ) -> ConfiguratorExtraResponseDTO:
        """Обновление характеристик опции администратором."""
        extra = await self.extra_repo.get_by_id(extra_id)
        if not extra:
            raise ConfiguratorExtraNotFound(
                f"ConfiguratorExtra with id {extra_id} not found."
            )

        if data.code is not None and data.code != extra.code:
            existing = await self.extra_repo.get_by_code(data.code)
            if existing:
                raise ConfiguratorExtraAlreadyExists(
                    f"ConfiguratorExtra with code '{data.code}' already exists."
                )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.extra_repo.update_extra(extra_id, update_data)
        await self.session.commit()

        updated_extra = await self.extra_repo.get_by_id(extra_id)
        return ConfiguratorExtraResponseDTO.model_validate(updated_extra)

    async def reorder_extra(
        self,
        extra_id: int,
        data: ConfiguratorExtraUpdateIndexDTO,
    ) -> ConfiguratorExtraResponseDTO:
        """Изменение позиции опции с автоматическим сдвигом соседей."""
        extra = await self.extra_repo.get_by_id(extra_id)
        if not extra:
            raise ConfiguratorExtraNotFound(
                f"ConfiguratorExtra with id {extra_id} not found."
            )

        if extra.index != data.new_index:
            await self.extra_repo.reorder_index(
                obj_id=extra_id,
                old_index=extra.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated_extra = await self.extra_repo.get_by_id(extra_id)
        return ConfiguratorExtraResponseDTO.model_validate(updated_extra)

    async def delete_extra(self, extra_id: int) -> None:
        """Удаление опции с проверкой зависимостей и сдвигом оставшихся индексов."""
        extra = await self.extra_repo.get_by_id(extra_id)
        if not extra:
            raise ConfiguratorExtraNotFound(
                f"ConfiguratorExtra with id {extra_id} not found."
            )

        has_deps = await self.extra_repo.has_dependencies(extra_id)
        if has_deps:
            raise ConfiguratorExtraHasDependencies(
                f"Cannot delete ConfiguratorExtra with id {extra_id} because it has dependencies."
            )

        deleted_index = extra.index
        await self.extra_repo.delete_extra(extra_id)
        await self.extra_repo.shift_indexes_after_delete(deleted_index=deleted_index)
        await self.session.commit()

    # ==================== Translations Operations ====================

    async def create_translation(
        self,
        extra_id: int,
        data: ConfiguratorExtraTranslationCreate,
    ) -> ConfiguratorExtraTranslationResponseDTO:
        """Добавление перевода к опции."""
        extra = await self.extra_repo.get_by_id(extra_id)
        if not extra:
            raise ConfiguratorExtraNotFound(
                f"ConfiguratorExtra with id {extra_id} not found."
            )

        existing = await self.translation_repo.get_by_extra_and_locale(extra_id, data.locale)
        if existing:
            raise ConfiguratorExtraTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for extra {extra_id}."
            )

        insert_dto = ConfiguratorExtraTranslationInsert(
            locale=data.locale,
            name=data.name,
            description=data.description,
            extra_id=extra_id,
        )
        new_trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        await self.session.refresh(new_trans)
        return ConfiguratorExtraTranslationResponseDTO.model_validate(new_trans)

    async def update_translation(
        self,
        translation_id: int,
        data: ConfiguratorExtraTranslationUpdate,
    ) -> ConfiguratorExtraTranslationResponseDTO:
        """Обновление перевода."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise ConfiguratorExtraTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()
        await self.session.refresh(trans)
        return ConfiguratorExtraTranslationResponseDTO.model_validate(trans)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода с запретом удаления последнего оставшегося (Правило 5.1)."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise ConfiguratorExtraTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        extra = await self.extra_repo.get_by_id(trans.extra_id)
        if extra and len(extra.translations) <= 1:
            raise ConfiguratorExtraTranslationDeleteError(
                "Cannot delete the only remaining translation of ConfiguratorExtra."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()

    def _to_localized_dto(
        self,
        extra,
        locale: Optional[Language],
    ) -> ConfiguratorExtraLocalizedResponseDTO:
        target_locale = locale or Language.ENG
        name = extra._get_field_with_translation(lambda t: t.name, target_locale)
        description = extra._get_field_with_translation(lambda t: t.description, target_locale)

        return ConfiguratorExtraLocalizedResponseDTO(
            id=extra.id,
            code=extra.code,
            price=float(extra.price),
            currency=extra.currency,
            billing_type=extra.billing_type,
            index=extra.index,
            is_active=extra.is_active,
            name=name if name else "No Translation",
            description=description,
            created_at=extra.created_at,
            updated_at=extra.updated_at,
        )
