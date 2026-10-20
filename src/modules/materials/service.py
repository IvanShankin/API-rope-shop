from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.materials.repository import (
    MaterialRepository,
    MaterialTranslationRepository,
)
from src.modules.materials.models_dto import (
    MaterialBase,
    MaterialCreate,
    MaterialUpdate,
    MaterialUpdateIndexDTO,
    MaterialResponseDTO,
    MaterialLocalizedResponseDTO,
    MaterialTranslationCreate,
    MaterialTranslationInsert,
    MaterialTranslationUpdate,
    MaterialTranslationResponseDTO,
)
from src.modules.materials.exception import (
    MaterialNotFound,
    MaterialAlreadyExists,
    MaterialValidationError,
    MaterialTranslationNotFound,
    MaterialTranslationAlreadyExists,
    MaterialTranslationDeleteError,
    MaterialHasDependencies,
    MaterialGroupNotFound,
)


class MaterialService:
    def __init__(
        self,
        material_repo: MaterialRepository,
        translation_repo: MaterialTranslationRepository,
        session: AsyncSession,
    ):
        self.material_repo = material_repo
        self.translation_repo = translation_repo
        self.session = session

    async def create_material(
        self,
        data: MaterialCreate
    ) -> MaterialResponseDTO:
        """Создание нового материала с обязательными переводами."""
        if not data.translations:
            raise MaterialValidationError(
                "At least one translation is required when creating a Material."
            )

        if not await self.material_repo.exists_material_group(data.material_group_id):
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {data.material_group_id} not found."
            )

        existing = await self.material_repo.get_by_code(data.code)
        if existing:
            raise MaterialAlreadyExists(
                f"Material with code '{data.code}' already exists."
            )

        # Проверка уникальности локалей в переданном списке
        locales = [t.locale for t in data.translations]
        if len(locales) != len(set(locales)):
            raise MaterialValidationError(
                "Duplicate locales found in translations."
            )

        if data.index is None:
            max_index = await self.material_repo.get_max_index(
                material_group_id=data.material_group_id
            )
            target_index = max_index + 1
        else:
            target_index = data.index
            await self.material_repo.shift_indexes_for_insert(
                target_index=target_index,
                material_group_id=data.material_group_id,
            )

        base_dto = MaterialBase(
            material_group_id=data.material_group_id,
            code=data.code,
            index=target_index,
            is_active=data.is_active,
        )
        new_material = await self.material_repo.add_material(base_dto)
        await self.session.flush()

        for trans_data in data.translations:
            insert_dto = MaterialTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                material_id=new_material.id,
            )
            await self.translation_repo.add_translation(insert_dto)

        await self.session.commit()
        created_material = await self.material_repo.get_by_id(new_material.id)
        return MaterialResponseDTO.model_validate(created_material)

    async def get_all_materials(
        self,
        material_group_id: Optional[int] = None,
        locale: Optional[Language] = None,
        is_active: Optional[bool] = None,
        is_admin: bool = False,
    ) -> List[MaterialLocalizedResponseDTO]:
        """Получение списка всех материалов с локализацией по указанному языку."""
        effective_active = is_active if is_admin else True
        materials = await self.material_repo.get_all(
            material_group_id=material_group_id,
            is_active=effective_active,
        )
        return [self._to_localized_dto(m, locale) for m in materials]

    async def get_material_by_id(
        self,
        material_id: int,
        is_admin: bool = False,
    ) -> MaterialResponseDTO:
        """Получение материала по ID со всеми переводами."""
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            raise MaterialNotFound(
                f"Material with id {material_id} not found."
            )
        if not is_admin and not material.is_active:
            raise MaterialNotFound(
                f"Material with id {material_id} not found."
            )
        return MaterialResponseDTO.model_validate(material)

    def _to_localized_dto(
        self,
        material,
        locale: Optional[Language]
    ) -> MaterialLocalizedResponseDTO:
        target_locale = locale or Language.ENG
        name = material._get_field_with_translation(lambda t: t.name, target_locale)

        return MaterialLocalizedResponseDTO(
            id=material.id,
            material_group_id=material.material_group_id,
            code=material.code,
            index=material.index,
            is_active=material.is_active,
            name=name if name else "No Translation",
        )

    async def update_material(
        self,
        material_id: int,
        data: MaterialUpdate
    ) -> MaterialResponseDTO:
        """Обновление характеристик материала."""
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            raise MaterialNotFound(
                f"Material with id {material_id} not found."
            )

        if data.code is not None and data.code != material.code:
            existing = await self.material_repo.get_by_code(data.code)
            if existing:
                raise MaterialAlreadyExists(
                    f"Material with code '{data.code}' already exists."
                )

        update_data = data.model_dump(exclude_unset=True)

        if data.material_group_id is not None and data.material_group_id != material.material_group_id:
            if not await self.material_repo.exists_material_group(data.material_group_id):
                raise MaterialGroupNotFound(
                    f"MaterialGroup with id {data.material_group_id} not found."
                )
            # Сдвигаем оставшиеся индексы в старой группе
            await self.material_repo.shift_indexes_after_delete(
                deleted_index=material.index,
                material_group_id=material.material_group_id,
            )
            # Помещаем в конец новой группы
            new_index = await self.material_repo.get_max_index(
                material_group_id=data.material_group_id
            ) + 1
            update_data["index"] = new_index

        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.material_repo.update_material(material_id, update_data)
        await self.session.commit()

        updated_material = await self.material_repo.get_by_id(material_id)
        return MaterialResponseDTO.model_validate(updated_material)

    async def reorder_material(
        self,
        material_id: int,
        data: MaterialUpdateIndexDTO
    ) -> MaterialResponseDTO:
        """Изменение позиции материала внутри группы с автоматическим сдвигом соседей."""
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            raise MaterialNotFound(
                f"Material with id {material_id} not found."
            )

        if material.index != data.new_index:
            await self.material_repo.reorder_index(
                obj_id=material_id,
                old_index=material.index,
                new_index=data.new_index,
                material_group_id=material.material_group_id,
            )
            await self.session.commit()

        updated_material = await self.material_repo.get_by_id(material_id)
        return MaterialResponseDTO.model_validate(updated_material)

    async def delete_material(self, material_id: int) -> None:
        """Удаление материала с проверкой правила 5.1 (наличие зависимостей)."""
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            raise MaterialNotFound(
                f"Material with id {material_id} not found."
            )

        has_deps = await self.material_repo.has_dependencies(material_id)
        if has_deps:
            raise MaterialHasDependencies(
                f"Cannot delete Material with id {material_id} because it has associated dependencies."
            )

        deleted_index = material.index
        group_id = material.material_group_id
        await self.material_repo.delete_material(material_id)
        await self.material_repo.shift_indexes_after_delete(
            deleted_index=deleted_index,
            material_group_id=group_id,
        )
        await self.session.commit()

    # ==================== Translations Operations ====================\n
    async def create_translation(
        self,
        material_id: int,
        data: MaterialTranslationCreate,
    ) -> MaterialTranslationResponseDTO:
        """Добавление перевода к материалу."""
        material = await self.material_repo.get_by_id(material_id)
        if not material:
            raise MaterialNotFound(
                f"Material with id {material_id} not found."
            )

        existing = await self.translation_repo.get_by_material_and_locale(material_id, data.locale)
        if existing:
            raise MaterialTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists."
            )

        insert_dto = MaterialTranslationInsert(
            locale=data.locale,
            name=data.name,
            material_id=material_id,
        )

        new_trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        await self.session.refresh(new_trans)
        return MaterialTranslationResponseDTO.model_validate(new_trans)

    async def update_translation(
        self,
        translation_id: int,
        data: MaterialTranslationUpdate,
    ) -> MaterialTranslationResponseDTO:
        """Обновление существующего перевода."""
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise MaterialTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()

        updated_trans = await self.translation_repo.get_by_id(translation_id)
        return MaterialTranslationResponseDTO.model_validate(updated_trans)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода с проверкой правила 5.1 (нельзя удалять последний оставшийся перевод)."""
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise MaterialTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        material = await self.material_repo.get_by_id(translation.material_id)
        if not material or len(material.translations) <= 1:
            raise MaterialTranslationDeleteError(
                "Cannot delete the last translation of a Material."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()
