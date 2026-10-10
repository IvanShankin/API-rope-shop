from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.material_groups.repository import (
    MaterialGroupRepository,
    MaterialGroupTranslationRepository,
)
from src.modules.material_groups.models_dto import (
    MaterialGroupBase,
    MaterialGroupCreate,
    MaterialGroupUpdate,
    MaterialGroupUpdateIndexDTO,
    MaterialGroupResponseDTO,
    MaterialGroupLocalizedResponseDTO,
    MaterialGroupTranslationCreate,
    MaterialGroupTranslationInsert,
    MaterialGroupTranslationUpdate,
    MaterialGroupTranslationResponseDTO,
)
from src.modules.material_groups.exception import (
    MaterialGroupNotFound,
    MaterialGroupAlreadyExists,
    MaterialGroupTranslationNotFound,
    MaterialGroupTranslationAlreadyExists,
    MaterialGroupTranslationDeleteError,
    MaterialGroupHasDependencies,
)


class MaterialGroupService:
    def __init__(
        self,
        group_repo: MaterialGroupRepository,
        translation_repo: MaterialGroupTranslationRepository,
        session: AsyncSession,
    ):
        self.group_repo = group_repo
        self.translation_repo = translation_repo
        self.session = session

    async def create_material_group(
        self,
        data: MaterialGroupCreate
    ) -> MaterialGroupResponseDTO:
        """Создание новой группы материалов с обязательными переводами."""
        if not data.translations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one translation is required when creating a MaterialGroup.",
            )

        existing = await self.group_repo.get_by_code(data.code)
        if existing:
            raise MaterialGroupAlreadyExists(
                f"MaterialGroup with code '{data.code}' already exists."
            )

        # Проверка уникальности локалей в переданном списке
        locales = [t.locale for t in data.translations]
        if len(locales) != len(set(locales)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate locales found in translations.",
            )

        if data.index is None:
            max_index = await self.group_repo.get_max_index()
            target_index = max_index + 1
        else:
            target_index = data.index
            await self.group_repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = MaterialGroupBase(
            code=data.code,
            index=target_index,
            is_active=data.is_active,
        )
        new_group = await self.group_repo.add_group(base_dto)
        await self.session.flush()

        for trans_data in data.translations:
            insert_dto = MaterialGroupTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                material_group_id=new_group.id,
            )
            await self.translation_repo.add_translation(insert_dto)

        await self.session.commit()
        created_group = await self.group_repo.get_by_group_id(new_group.id)
        return MaterialGroupResponseDTO.model_validate(created_group)

    async def get_all_material_groups(
        self,
        locale: Optional[Language] = None,
        is_active: Optional[bool] = None,
    ) -> List[MaterialGroupLocalizedResponseDTO]:
        """Получение списка всех групп с локализацией по указанному языку."""
        groups = await self.group_repo.get_all(is_active=is_active)
        return [self._to_localized_dto(g, locale) for g in groups]

    async def get_material_group_by_id(
        self,
        group_id: int
    ) -> MaterialGroupResponseDTO:
        """Получение группы материалов по ID со всеми переводами."""
        group = await self.group_repo.get_by_group_id(group_id)
        if not group:
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {group_id} not found."
            )
        return MaterialGroupResponseDTO.model_validate(group)

    def _to_localized_dto(
        self,
        group,
        locale: Optional[Language]
    ) -> MaterialGroupLocalizedResponseDTO:
        target_locale = locale or Language.ENG
        name = group._get_field_with_translation(lambda t: t.name, target_locale)

        return MaterialGroupLocalizedResponseDTO(
            id=group.id,
            code=group.code,
            index=group.index,
            is_active=group.is_active,
            name=name if name else "No Translation",
        )

    async def update_material_group(
        self,
        group_id: int,
        data: MaterialGroupUpdate
    ) -> MaterialGroupResponseDTO:
        """Обновление характеристик группы материалов."""
        group = await self.group_repo.get_by_group_id(group_id)
        if not group:
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {group_id} not found."
            )

        if data.code is not None and data.code != group.code:
            existing = await self.group_repo.get_by_code(data.code)
            if existing:
                raise MaterialGroupAlreadyExists(
                    f"MaterialGroup with code '{data.code}' already exists."
                )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.group_repo.update_group(group_id, update_data)
        await self.session.commit()

        updated_group = await self.group_repo.get_by_group_id(group_id)
        return MaterialGroupResponseDTO.model_validate(updated_group)

    async def reorder_material_group(
        self,
        group_id: int,
        data: MaterialGroupUpdateIndexDTO
    ) -> MaterialGroupResponseDTO:
        """Изменение позиции группы материалов с автоматическим сдвигом соседей."""
        group = await self.group_repo.get_by_group_id(group_id)
        if not group:
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {group_id} not found."
            )

        if group.index != data.new_index:
            await self.group_repo.reorder_index(
                obj_id=group_id,
                old_index=group.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated_group = await self.group_repo.get_by_group_id(group_id)
        return MaterialGroupResponseDTO.model_validate(updated_group)

    async def delete_material_group(self, group_id: int) -> None:
        """Удаление группы материалов с проверкой правила 5.1 (наличие зависимостей)."""
        group = await self.group_repo.get_by_group_id(group_id)
        if not group:
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {group_id} not found."
            )

        has_deps = await self.group_repo.has_dependencies(group_id)
        if has_deps:
            raise MaterialGroupHasDependencies(
                f"Cannot delete MaterialGroup with id {group_id} because it has associated dependencies."
            )

        deleted_index = group.index
        await self.group_repo.delete_group(group_id)
        await self.group_repo.shift_indexes_after_delete(deleted_index=deleted_index)
        await self.session.commit()

    # ==================== Translations Operations ====================

    async def create_translation(
        self,
        group_id: int,
        data: MaterialGroupTranslationCreate,
    ) -> MaterialGroupTranslationResponseDTO:
        """Добавление перевода к группе материалов."""
        group = await self.group_repo.get_by_group_id(group_id)
        if not group:
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {group_id} not found."
            )

        existing = await self.translation_repo.get_by_group_and_locale(group_id, data.locale)
        if existing:
            raise MaterialGroupTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists."
            )

        insert_dto = MaterialGroupTranslationInsert(
            locale=data.locale,
            name=data.name,
            material_group_id=group_id,
        )

        new_trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        await self.session.refresh(new_trans)
        return MaterialGroupTranslationResponseDTO.model_validate(new_trans)

    async def update_translation(
        self,
        translation_id: int,
        data: MaterialGroupTranslationUpdate,
    ) -> MaterialGroupTranslationResponseDTO:
        """Обновление существующего перевода."""
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise MaterialGroupTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()

        updated_trans = await self.translation_repo.get_by_id(translation_id)
        return MaterialGroupTranslationResponseDTO.model_validate(updated_trans)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода с проверкой правила 5.1 (нельзя удалять последний оставшийся перевод)."""
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise MaterialGroupTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        group = await self.group_repo.get_by_group_id(translation.material_group_id)
        if not group or len(group.translations) <= 1:
            raise MaterialGroupTranslationDeleteError(
                "Cannot delete the last translation of a MaterialGroup."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()
