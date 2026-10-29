from pathlib import Path
import uuid
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import DEFAULT_LOCALE, Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.service import PathBuilder
from src.modules.charity_photos.exception import (
    CharityPhotoHasDependencies,
    CharityPhotoNotFound,
    CharityPhotoTranslationAlreadyExists,
    CharityPhotoTranslationDeleteError,
    CharityPhotoTranslationNotFound,
)
from src.modules.charity_photos.models import CharityPhoto
from src.modules.charity_photos.models_dto import (
    CharityPhotoBaseDTO,
    CharityPhotoResponseDTO,
    CharityPhotoTranslationCreate,
    CharityPhotoTranslationInsert,
    CharityPhotoTranslationResponseDTO,
    CharityPhotoTranslationUpdate,
    CreateCharityPhotoRequestDTO,
    UpdateCharityPhotoIndexRequestDTO,
    UpdateCharityPhotoRequestDTO,
)
from src.modules.charity_photos.repository import (
    CharityPhotoRepository,
    CharityPhotoTranslationRepository,
)


class CharityPhotoService:
    def __init__(
        self,
        repo: CharityPhotoRepository,
        translation_repo: CharityPhotoTranslationRepository,
        session: AsyncSession,
        image_manager: ImageManager,
        path_builder: PathBuilder,
    ):
        self.repo = repo
        self.translation_repo = translation_repo
        self.session = session
        self.image_manager = image_manager
        self.path_builder = path_builder

    def _to_response_dto(
        self, photo: CharityPhoto, locale: Optional[Language] = None
    ) -> CharityPhotoResponseDTO:
        """Преобразование модели CharityPhoto в CharityPhotoResponseDTO с локализацией."""
        target_locale = locale or DEFAULT_LOCALE
        title = photo._get_field_with_translation(
            lambda t: t.title, target_locale, fallback=Language.ENG
        )
        description = photo._get_field_with_translation(
            lambda t: t.description, target_locale, fallback=Language.ENG
        )

        matched_locale: Optional[Language] = None
        if photo.translations:
            target_norm = CharityPhoto._normalize_locale(target_locale)
            for t in photo.translations:
                if CharityPhoto._normalize_locale(t.locale) == target_norm:
                    matched_locale = t.locale
                    break
            if not matched_locale:
                fallback_norm = CharityPhoto._normalize_locale(Language.ENG)
                for t in photo.translations:
                    if CharityPhoto._normalize_locale(t.locale) == fallback_norm:
                        matched_locale = t.locale
                        break
            if not matched_locale and photo.translations:
                matched_locale = photo.translations[0].locale

        return CharityPhotoResponseDTO(
            id=photo.id,
            image_url=photo.image_url,
            title=title,
            description=description,
            locale=matched_locale,
            translations=[
                CharityPhotoTranslationResponseDTO.model_validate(t)
                for t in photo.translations
            ] if photo.translations else [],
            index=photo.index,
            is_active=photo.is_active,
            created_at=photo.created_at,
            updated_at=photo.updated_at,
        )

    async def create_photo(
        self, data: CreateCharityPhotoRequestDTO
    ) -> CharityPhotoResponseDTO:
        """Создание новой записи фотографии благотворительности через DTO."""
        count = await self.repo.count()
        if data.index is None:
            max_index = await self.repo.get_max_index()
            target_index = 0 if count == 0 else max_index + 1
        else:
            target_index = data.index
            await self.repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = CharityPhotoBaseDTO(
            image_url=data.image_url,
            index=target_index,
            is_active=data.is_active,
        )
        new_photo = self.repo.add_photo(base_dto)
        await self.session.flush()

        if data.translations:
            for tr in data.translations:
                self.translation_repo.add_translation(
                    CharityPhotoTranslationInsert(
                        charity_photo_id=new_photo.id,
                        locale=tr.locale,
                        title=tr.title,
                        description=tr.description,
                    )
                )
        elif data.title is not None or data.description is not None:
            self.translation_repo.add_translation(
                CharityPhotoTranslationInsert(
                    charity_photo_id=new_photo.id,
                    locale=data.locale,
                    title=data.title,
                    description=data.description,
                )
            )

        await self.session.commit()

        loaded = await self.repo.get_by_id(new_photo.id)
        return self._to_response_dto(loaded, locale=data.locale)

    async def upload_photo(
        self,
        file: UploadFile,
        title: Optional[str] = None,
        description: Optional[str] = None,
        locale: Language = Language.ENG,
        index: Optional[int] = None,
        is_active: bool = True,
    ) -> CharityPhotoResponseDTO:
        """Загрузка файла, оптимизация в WebP и сохранение новой фотографии благотворительности с переводом."""
        count = await self.repo.count()
        if index is None:
            max_index = await self.repo.get_max_index()
            target_index = 0 if count == 0 else max_index + 1
        else:
            target_index = index
            await self.repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = CharityPhotoBaseDTO(
            image_url="",
            index=target_index,
            is_active=is_active,
        )
        new_photo = self.repo.add_photo(base_dto)
        await self.session.flush()

        file_name = f"img_{uuid.uuid4().hex[:10]}"
        dest = self.path_builder.get_charity_photo(
            charity_photo_id=new_photo.id, file_name=file_name
        )
        file_ext = Path(file.filename or "").suffix.lstrip(".").lower() or "jpg"
        orig_dest = self.path_builder.get_charity_photo_original(
            charity_photo_id=new_photo.id, file_name=file_name, file_type=file_ext
        )
        saved_path = await self.image_manager.save_image(
            file=file,
            destination=dest,
            original_destination=orig_dest,
        )
        media_url = self.image_manager.to_media_url(saved_path)

        new_photo.image_url = media_url

        if title is not None or description is not None:
            self.translation_repo.add_translation(
                CharityPhotoTranslationInsert(
                    charity_photo_id=new_photo.id,
                    locale=locale,
                    title=title,
                    description=description,
                )
            )

        await self.session.commit()

        loaded = await self.repo.get_by_id(new_photo.id)
        return self._to_response_dto(loaded, locale=locale)

    async def upload_image_for_photo(
        self,
        photo_id: int,
        file: UploadFile,
    ) -> CharityPhotoResponseDTO:
        """Замена файла изображения для существующей фотографии благотворительности."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")

        if photo.image_url and self.image_manager:
            self.image_manager.delete_image(photo.image_url)

        file_name = f"img_{uuid.uuid4().hex[:10]}"
        dest = self.path_builder.get_charity_photo(
            charity_photo_id=photo_id, file_name=file_name
        )
        file_ext = Path(file.filename or "").suffix.lstrip(".").lower() or "jpg"
        orig_dest = self.path_builder.get_charity_photo_original(
            charity_photo_id=photo_id, file_name=file_name, file_type=file_ext
        )
        saved_path = await self.image_manager.save_image(
            file=file,
            destination=dest,
            original_destination=orig_dest,
        )
        media_url = self.image_manager.to_media_url(saved_path)

        await self.repo.update_photo(photo_id, {"image_url": media_url})
        await self.session.commit()

        loaded = await self.repo.get_by_id(photo_id)
        return self._to_response_dto(loaded)

    async def get_photos(
        self,
        is_active: Optional[bool] = None,
        locale: Optional[Language] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        is_admin: bool = False,
    ) -> List[CharityPhotoResponseDTO]:
        """Получение списка фотографий благотворительности, отсортированных по index."""
        effective_active = is_active if is_admin else True
        photos = await self.repo.get_all(
            is_active=effective_active,
            skip=skip,
            limit=limit,
        )
        return [self._to_response_dto(p, locale=locale) for p in photos]

    async def get_photo_by_id(
        self, photo_id: int, locale: Optional[Language] = None, is_admin: bool = False
    ) -> CharityPhotoResponseDTO:
        """Получение фотографии благотворительности по ID."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")
        if not is_admin and not photo.is_active:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")
        return self._to_response_dto(photo, locale=locale)

    async def update_photo(
        self,
        photo_id: int,
        data: Optional[UpdateCharityPhotoRequestDTO] = None,
        file: Optional[UploadFile] = None,
        locale: Optional[Language] = None,
    ) -> CharityPhotoResponseDTO:
        """Обновление атрибутов фотографии благотворительности и/или замена файла."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")

        target_locale = (data.locale if data and data.locale else None) or locale or Language.ENG
        update_dict = {}

        if data and data.is_active is not None:
            update_dict["is_active"] = data.is_active

        has_translation_data = False
        title_val = data.title if data else None
        desc_val = data.description if data else None

        if data and (title_val is not None or desc_val is not None):
            has_translation_data = True

        if not update_dict and not has_translation_data and file is None:
            raise NoDataForUpdate("No data provided for update.")

        if file is not None:
            if photo.image_url and self.image_manager:
                self.image_manager.delete_image(photo.image_url)

            file_name = f"img_{uuid.uuid4().hex[:10]}"
            dest = self.path_builder.get_charity_photo(
                charity_photo_id=photo_id, file_name=file_name
            )
            saved_path = await self.image_manager.save_image(file=file, destination=dest)
            update_dict["image_url"] = self.image_manager.to_media_url(saved_path)

        if update_dict:
            await self.repo.update_photo(photo_id, update_dict)

        if has_translation_data:
            existing_tr = await self.translation_repo.get_by_photo_id_and_locale(
                photo_id=photo_id, locale=target_locale
            )
            if existing_tr:
                tr_update = {}
                if title_val is not None:
                    tr_update["title"] = title_val
                if desc_val is not None:
                    tr_update["description"] = desc_val
                if tr_update:
                    await self.translation_repo.update_translation(existing_tr.id, tr_update)
            else:
                self.translation_repo.add_translation(
                    CharityPhotoTranslationInsert(
                        charity_photo_id=photo_id,
                        locale=target_locale,
                        title=title_val,
                        description=desc_val,
                    )
                )

        await self.session.commit()

        updated = await self.repo.get_by_id(photo_id)
        return self._to_response_dto(updated, locale=target_locale)

    async def reorder_photo(
        self,
        photo_id: int,
        data: UpdateCharityPhotoIndexRequestDTO,
    ) -> CharityPhotoResponseDTO:
        """Перемещение позиции фотографии благотворительности со сдвигом соседей."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")

        if photo.index != data.new_index:
            await self.repo.reorder_index(
                obj_id=photo_id,
                old_index=photo.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated = await self.repo.get_by_id(photo_id)
        return self._to_response_dto(updated)

    async def delete_photo(self, photo_id: int) -> None:
        """Удаление фотографии благотворительности с диска и из БД со сдвигом последующих индексов."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")

        has_deps = await self.repo.has_dependencies(photo_id)
        if has_deps:
            raise CharityPhotoHasDependencies(
                f"Cannot delete CharityPhoto {photo_id}: it has dependent records."
            )

        deleted_index = photo.index
        image_url = photo.image_url

        if image_url and self.image_manager:
            self.image_manager.delete_image(image_url)

        await self.repo.delete_photo(photo_id)
        await self.repo.shift_indexes_after_delete(deleted_index=deleted_index)
        await self.session.commit()

    # ==================== Translation Management ====================

    async def add_translation(
        self, photo_id: int, data: CharityPhotoTranslationCreate
    ) -> CharityPhotoTranslationResponseDTO:
        """Добавление нового перевода для фотографии благотворительности."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")

        existing = await self.translation_repo.get_by_photo_id_and_locale(
            photo_id=photo_id, locale=data.locale
        )
        if existing:
            raise CharityPhotoTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for CharityPhoto {photo_id}."
            )

        new_tr = self.translation_repo.add_translation(
            CharityPhotoTranslationInsert(
                charity_photo_id=photo_id,
                locale=data.locale,
                title=data.title,
                description=data.description,
            )
        )
        await self.session.commit()
        await self.session.refresh(new_tr)
        return CharityPhotoTranslationResponseDTO.model_validate(new_tr)

    async def update_translation(
        self, photo_id: int, translation_id: int, data: CharityPhotoTranslationUpdate
    ) -> CharityPhotoTranslationResponseDTO:
        """Обновление существующего перевода фотографии благотворительности."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")

        tr = await self.translation_repo.get_by_id(translation_id)
        if not tr or tr.charity_photo_id != photo_id:
            raise CharityPhotoTranslationNotFound(
                f"Translation with id {translation_id} not found for CharityPhoto {photo_id}."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("No translation data provided for update.")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()
        await self.session.refresh(tr)
        return CharityPhotoTranslationResponseDTO.model_validate(tr)

    async def delete_translation(self, photo_id: int, translation_id: int) -> None:
        """Удаление перевода фотографии благотворительности. Запрещено удалять единственный перевод."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise CharityPhotoNotFound(f"CharityPhoto with id {photo_id} not found.")

        tr = await self.translation_repo.get_by_id(translation_id)
        if not tr or tr.charity_photo_id != photo_id:
            raise CharityPhotoTranslationNotFound(
                f"Translation with id {translation_id} not found for CharityPhoto {photo_id}."
            )

        count = await self.translation_repo.count_by_photo_id(photo_id)
        if count <= 1:
            raise CharityPhotoTranslationDeleteError(
                "Cannot delete the only remaining translation for this photo."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()
