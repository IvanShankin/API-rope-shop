from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import DEFAULT_LOCALE, Language
from src.modules.colors.repository import ColorRepository, ColorTranslationRepository
from src.modules.colors.models_dto import (
    ColorBase,
    ColorCreate,
    ColorUpdate,
    ColorUpdateIndexDTO,
    ColorResponseDTO,
    ColorLocalizedResponseDTO,
    ColorTranslationCreate,
    ColorTranslationInsert,
    ColorTranslationUpdate,
    ColorTranslationResponseDTO,
)
from src.modules.colors.exception import (
    ColorNotFound,
    ColorAlreadyExists,
    ColorValidationError,
    ColorTranslationNotFound,
    ColorTranslationAlreadyExists,
    ColorTranslationDeleteError,
    ColorHasDependencies,
)


class ColorService:
    def __init__(
        self,
        color_repo: ColorRepository,
        translation_repo: ColorTranslationRepository,
        session: AsyncSession,
    ):
        self.color_repo = color_repo
        self.translation_repo = translation_repo
        self.session = session

    async def create_color(self, data: ColorCreate) -> ColorResponseDTO:
        if not data.translations:
            raise ColorValidationError(
                "At least one translation is required when creating a Color."
            )

        existing = await self.color_repo.get_by_code(data.code)
        if existing:
            raise ColorAlreadyExists(f"Color with code '{data.code}' already exists.")

        # Сдвигаем существующие цвета с индексом >= data.index на +1, освобождая позицию
        await self.color_repo.shift_indexes_for_insert(target_index=data.index)

        base_color_dto = ColorBase(
            code=data.code,
            hex=data.hex,
            index=data.index,
            is_active=data.is_active,
        )
        new_color = await self.color_repo.add_color(base_color_dto)
        await self.session.flush()

        for trans_data in data.translations:
            insert_dto = ColorTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                color_id=new_color.id,
            )
            await self.translation_repo.add_translation(insert_dto)

        await self.session.commit()
        created_color = await self.color_repo.get_by_id(new_color.id)
        return ColorResponseDTO.model_validate(created_color)

    async def get_all_colors(
        self,
        locale: Optional[Language] = None,
        is_active: Optional[bool] = None,
        is_admin: bool = False,
    ) -> List[ColorLocalizedResponseDTO]:
        effective_active = is_active if is_admin else True
        colors = await self.color_repo.get_all(is_active=effective_active)
        return [self._to_localized_dto(c, locale) for c in colors]

    async def get_color_by_id(
        self, color_id: int, is_admin: bool = False
    ) -> ColorResponseDTO:
        color = await self.color_repo.get_by_id(color_id)
        if not color:
            raise ColorNotFound(f"Color with id {color_id} not found.")
        if not is_admin and not color.is_active:
            raise ColorNotFound(f"Color with id {color_id} not found.")
        return ColorResponseDTO.model_validate(color)

    def _to_localized_dto(self, color, locale: Optional[Language]) -> ColorLocalizedResponseDTO:
        target_locale = locale if locale else DEFAULT_LOCALE
        name = color._get_field_with_translation(lambda t: t.name, target_locale)

        return ColorLocalizedResponseDTO(
            id=color.id,
            code=color.code,
            hex=color.hex,
            index=color.index,
            is_active=color.is_active,
            name=name if name else "No Translation",
        )

    async def update_color(self, color_id: int, data: ColorUpdate) -> ColorResponseDTO:
        color = await self.color_repo.get_by_id(color_id)
        if not color:
            raise ColorNotFound(f"Color with id {color_id} not found.")

        if data.code is not None and data.code != color.code:
            existing = await self.color_repo.get_by_code(data.code)
            if existing:
                raise ColorAlreadyExists(f"Color with code '{data.code}' already exists.")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self.color_repo.update_color(color_id, update_data)
            await self.session.commit()

        updated_color = await self.color_repo.get_by_id(color_id)
        return ColorResponseDTO.model_validate(updated_color)

    async def reorder_color(self, color_id: int, data: ColorUpdateIndexDTO) -> ColorResponseDTO:
        """Специализированное обновление порядка отображения (индекса) со сдвигом соседей."""
        color = await self.color_repo.get_by_id(color_id)
        if not color:
            raise ColorNotFound(f"Color with id {color_id} not found.")

        if color.index != data.new_index:
            await self.color_repo.reorder_index(
                obj_id=color_id,
                old_index=color.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated_color = await self.color_repo.get_by_id(color_id)
        return ColorResponseDTO.model_validate(updated_color)

    async def delete_color(self, color_id: int) -> None:
        color = await self.color_repo.get_by_id(color_id)
        if not color:
            raise ColorNotFound(f"Color with id {color_id} not found.")

        has_deps = await self.color_repo.has_dependencies(color_id)
        if has_deps:
            raise ColorHasDependencies(
                f"Cannot delete Color with id {color_id} because it is referenced by rope products."
            )

        deleted_index = color.index
        await self.color_repo.delete_color(color_id)
        # Сдвигаем оставшиеся индексы > deleted_index на -1 для заполнения пробела
        await self.color_repo.shift_indexes_after_delete(deleted_index=deleted_index)
        await self.session.commit()

    # Translations
    async def create_translation(
        self,
        color_id: int,
        data: ColorTranslationCreate,
    ) -> ColorTranslationResponseDTO:
        color = await self.color_repo.get_by_id(color_id)
        if not color:
            raise ColorNotFound(f"Color with id {color_id} not found.")

        existing = await self.translation_repo.get_by_color_and_locale(color_id, data.locale)
        if existing:
            raise ColorTranslationAlreadyExists(f"Translation for locale '{data.locale.value}' already exists.")

        insert_dto = ColorTranslationInsert(
            locale=data.locale,
            name=data.name,
            color_id=color_id,
        )

        new_trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        await self.session.refresh(new_trans)
        return ColorTranslationResponseDTO.model_validate(new_trans)

    async def update_translation(
        self,
        translation_id: int,
        data: ColorTranslationUpdate,
    ) -> ColorTranslationResponseDTO:
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise ColorTranslationNotFound(f"Translation with id {translation_id} not found.")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self.translation_repo.update_translation(translation_id, update_data)
            await self.session.commit()

        updated_trans = await self.translation_repo.get_by_id(translation_id)
        return ColorTranslationResponseDTO.model_validate(updated_trans)

    async def delete_translation(self, translation_id: int) -> None:
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise ColorTranslationNotFound(f"Translation with id {translation_id} not found.")

        color = await self.color_repo.get_by_id(translation.color_id)
        if len(color.translations) <= 1:
            raise ColorTranslationDeleteError("Cannot delete the last translation of a Color.")

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()
