from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from src.modules.base.database_model import Language
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.service import PathBuilder
from src.modules.splice_types.repository import SpliceTypeRepository, SpliceTypeTranslationRepository
from src.modules.splice_types.models import SpliceCategory
from src.modules.splice_types.models_dto import (
    SpliceTypeBase,
    SpliceTypeCreate,
    SpliceTypeUpdate,
    SpliceTypeResponseDTO,
    SpliceTypeLocalizedResponseDTO,
    SpliceTypeTranslationCreate,
    SpliceTypeTranslationInsert,
    SpliceTypeTranslationUpdate,
    SpliceTypeTranslationResponseDTO
)
from src.modules.splice_types.exception import (
    SpliceTypeNotFound,
    SpliceTypeAlreadyExists,
    SpliceTypeValidationError,
    SpliceTypeTranslationNotFound,
    SpliceTypeTranslationAlreadyExists,
    SpliceTypeTranslationDeleteError,
    SpliceTypeHasDependencies,
)


class SpliceTypeService:
    def __init__(
        self,
        type_repo: SpliceTypeRepository,
        translation_repo: SpliceTypeTranslationRepository,
        session: AsyncSession,
        image_manager: ImageManager,
        path_builder: PathBuilder,
    ):
        self.type_repo = type_repo
        self.translation_repo = translation_repo
        self.session = session
        self.image_manager = image_manager
        self.path_builder = path_builder

    async def create_splice_type(self, data: SpliceTypeCreate) -> SpliceTypeResponseDTO:
        if not data.translations:
            raise SpliceTypeValidationError("At least one translation is required when creating a SpliceType.")

        existing = await self.type_repo.get_by_code(data.code)
        if existing:
            raise SpliceTypeAlreadyExists(f"SpliceType with code '{data.code}' already exists.")
            
        base_type_dto = SpliceTypeBase(
            code=data.code,
            category=data.category,
            visual_type=data.visual_type,
            image_url=None,
            index=data.index,
            is_active=data.is_active
        )
        new_type = await self.type_repo.add_type(base_type_dto)
        await self.session.flush()
        
        for trans_data in data.translations:
            insert_dto = SpliceTypeTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                description=trans_data.description,
                splice_type_id=new_type.id
            )
            await self.translation_repo.add_translation(insert_dto)
            
        await self.session.commit()
        created_type = await self.type_repo.get_by_id(new_type.id)
        return SpliceTypeResponseDTO.model_validate(created_type)

    async def get_all_splice_types(self, locale: Optional[Language] = None, is_active: Optional[bool] = None) -> List[SpliceTypeLocalizedResponseDTO]:
        types = await self.type_repo.get_all(is_active=is_active)
        return [self._to_localized_dto(t, locale) for t in types]

    async def get_splice_types_by_category(self, category: SpliceCategory, locale: Optional[Language] = None, is_active: Optional[bool] = None) -> List[SpliceTypeLocalizedResponseDTO]:
        types = await self.type_repo.get_by_category(category=category, is_active=is_active)
        return [self._to_localized_dto(t, locale) for t in types]

    async def get_splice_type_by_id(self, type_id: int) -> SpliceTypeResponseDTO:
        """Метод для админки (возвращает все переводы)"""
        splice_type = await self.type_repo.get_by_id(type_id)
        if not splice_type:
            raise SpliceTypeNotFound(f"SpliceType with id {type_id} not found.")
        return SpliceTypeResponseDTO.model_validate(splice_type)

    def _to_localized_dto(self, splice_type, locale: Optional[Language]) -> SpliceTypeLocalizedResponseDTO:
        """Вспомогательный метод для конвертации модели БД в локализованное DTO"""
        target_locale = locale if locale else Language.ENG
        name = splice_type._get_field_with_translation(lambda t: t.name, target_locale)
        description = splice_type._get_field_with_translation(lambda t: t.description, target_locale)
        
        return SpliceTypeLocalizedResponseDTO(
            id=splice_type.id,
            created_at=splice_type.created_at,
            updated_at=splice_type.updated_at,
            code=splice_type.code,
            category=splice_type.category,
            visual_type=splice_type.visual_type,
            image_url=splice_type.image_url,
            index=splice_type.index,
            is_active=splice_type.is_active,
            name=name if name else "No Translation",
            description=description
        )

    async def update_splice_type(self, type_id: int, data: SpliceTypeUpdate) -> SpliceTypeResponseDTO:
        splice_type = await self.type_repo.get_by_id(type_id)
        if not splice_type:
            raise SpliceTypeNotFound(f"SpliceType with id {type_id} not found.")

        if data.code is not None and data.code != splice_type.code:
            existing = await self.type_repo.get_by_code(data.code)
            if existing:
                raise SpliceTypeAlreadyExists(f"SpliceType with code '{data.code}' already exists.")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self.type_repo.update_type(type_id, update_data)
            await self.session.commit()
            
        updated_type = await self.type_repo.get_by_id(type_id)
        return SpliceTypeResponseDTO.model_validate(updated_type)

    async def upload_image(self, type_id: int, file: UploadFile) -> SpliceTypeResponseDTO:
        """Загрузка, конвертация в WebP и сохранение изображения для услуги."""
        if not self.image_manager or not self.path_builder:
            raise RuntimeError("ImageManager or PathBuilder is not configured.")

        splice_type = await self.type_repo.get_by_id(type_id)
        if not splice_type:
            raise SpliceTypeNotFound(f"SpliceType with id {type_id} not found.")

        # Удаляем старое изображение, если оно было
        if splice_type.image_url:
            self.image_manager.delete_image(splice_type.image_url)

        # Вычисляем целевой путь
        dest = self.path_builder.get_splice_type(splice_type_id=type_id, file_name="image")
        file_ext = Path(file.filename or "").suffix.lstrip(".").lower() or "jpg"
        orig_dest = self.path_builder.get_splice_type_original(
            product_id=type_id, file_name="image", file_type=file_ext
        )

        # Конвертируем и сохраняем
        saved_path = await self.image_manager.save_image(
            file=file,
            destination=dest,
            original_destination=orig_dest,
        )
        media_url = self.image_manager.to_media_url(saved_path)

        # Обновляем запись в БД
        await self.type_repo.update_type(type_id, {"image_url": media_url})
        await self.session.commit()

        updated_type = await self.type_repo.get_by_id(type_id)
        return SpliceTypeResponseDTO.model_validate(updated_type)

    async def delete_image(self, type_id: int) -> SpliceTypeResponseDTO:
        """Удаление изображения услуги."""
        splice_type = await self.type_repo.get_by_id(type_id)
        if not splice_type:
            raise SpliceTypeNotFound(f"SpliceType with id {type_id} not found.")

        if splice_type.image_url and self.image_manager:
            self.image_manager.delete_image(splice_type.image_url)

        await self.type_repo.update_type(type_id, {"image_url": None})
        await self.session.commit()

        updated_type = await self.type_repo.get_by_id(type_id)
        return SpliceTypeResponseDTO.model_validate(updated_type)

    async def delete_splice_type(self, type_id: int) -> None:
        splice_type = await self.type_repo.get_by_id(type_id)
        if not splice_type:
            raise SpliceTypeNotFound(f"SpliceType with id {type_id} not found.")

        has_deps = await self.type_repo.has_dependencies(type_id)
        if has_deps:
            raise SpliceTypeHasDependencies(
                f"Cannot delete SpliceType with id {type_id} because it is referenced by splice price rules or rope products."
            )

        # Удаляем изображение с диска, если есть
        if splice_type.image_url and self.image_manager:
            self.image_manager.delete_image(splice_type.image_url)

        await self.type_repo.delete_type(type_id)
        await self.session.commit()

    # Translations
    async def create_translation(self, type_id: int, data: SpliceTypeTranslationCreate) -> SpliceTypeTranslationResponseDTO:
        splice_type = await self.type_repo.get_by_id(type_id)
        if not splice_type:
            raise SpliceTypeNotFound(f"SpliceType with id {type_id} not found.")
            
        existing = await self.translation_repo.get_by_type_and_locale(type_id, data.locale)
        if existing:
            raise SpliceTypeTranslationAlreadyExists(f"Translation for locale '{data.locale.value}' already exists.")
            
        insert_dto = SpliceTypeTranslationInsert(
            locale=data.locale,
            name=data.name,
            description=data.description,
            splice_type_id=type_id
        )
        
        new_trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        await self.session.refresh(new_trans)
        return SpliceTypeTranslationResponseDTO.model_validate(new_trans)

    async def update_translation(self, translation_id: int, data: SpliceTypeTranslationUpdate) -> SpliceTypeTranslationResponseDTO:
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise SpliceTypeTranslationNotFound(f"Translation with id {translation_id} not found.")
            
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self.translation_repo.update_translation(translation_id, update_data)
            await self.session.commit()
            
        updated_trans = await self.translation_repo.get_by_id(translation_id)
        return SpliceTypeTranslationResponseDTO.model_validate(updated_trans)

    async def delete_translation(self, translation_id: int) -> None:
        translation = await self.translation_repo.get_by_id(translation_id)
        if not translation:
            raise SpliceTypeTranslationNotFound(f"Translation with id {translation_id} not found.")
            
        splice_type = await self.type_repo.get_by_id(translation.splice_type_id)
        if len(splice_type.translations) <= 1:
            raise SpliceTypeTranslationDeleteError("Cannot delete the last translation of a SpliceType.")
            
        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()
