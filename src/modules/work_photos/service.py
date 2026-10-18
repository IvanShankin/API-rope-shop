import uuid
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.service import PathBuilder
from src.modules.work_photos.exception import (
    WorkPhotoHasDependencies,
    WorkPhotoNotFound,
    WorkPhotoTranslationAlreadyExists,
    WorkPhotoTranslationDeleteError,
    WorkPhotoTranslationNotFound,
)
from src.modules.work_photos.models import WorkPhoto
from src.modules.work_photos.models_dto import (
    CreateWorkPhotoRequestDTO,
    UpdateWorkPhotoIndexRequestDTO,
    UpdateWorkPhotoRequestDTO,
    WorkPhotoBaseDTO,
    WorkPhotoResponseDTO,
    WorkPhotoTranslationCreate,
    WorkPhotoTranslationInsert,
    WorkPhotoTranslationResponseDTO,
    WorkPhotoTranslationUpdate,
)
from src.modules.work_photos.repository import (
    WorkPhotoRepository,
    WorkPhotoTranslationRepository,
)


class WorkPhotoService:
    def __init__(
        self,
        repo: WorkPhotoRepository,
        translation_repo: WorkPhotoTranslationRepository,
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
        self, photo: WorkPhoto, locale: Optional[Language] = None
    ) -> WorkPhotoResponseDTO:
        """Преобразование модели WorkPhoto в WorkPhotoResponseDTO с локализацией."""
        target_locale = locale or Language.ENG
        title = photo._get_field_with_translation(
            lambda t: t.title, target_locale, fallback=Language.ENG
        )
        description = photo._get_field_with_translation(
            lambda t: t.description, target_locale, fallback=Language.ENG
        )

        matched_locale: Optional[Language] = None
        if photo.translations:
            target_norm = WorkPhoto._normalize_locale(target_locale)
            for t in photo.translations:
                if WorkPhoto._normalize_locale(t.locale) == target_norm:
                    matched_locale = t.locale
                    break
            if not matched_locale:
                fallback_norm = WorkPhoto._normalize_locale(Language.ENG)
                for t in photo.translations:
                    if WorkPhoto._normalize_locale(t.locale) == fallback_norm:
                        matched_locale = t.locale
                        break
            if not matched_locale and photo.translations:
                matched_locale = photo.translations[0].locale

        return WorkPhotoResponseDTO(
            id=photo.id,
            image_url=photo.image_url,
            title=title,
            description=description,
            locale=matched_locale,
            translations=[
                WorkPhotoTranslationResponseDTO.model_validate(t)
                for t in photo.translations
            ] if photo.translations else [],
            index=photo.index,
            is_active=photo.is_active,
            created_at=photo.created_at,
            updated_at=photo.updated_at,
        )

    async def create_photo(
        self, data: CreateWorkPhotoRequestDTO
    ) -> WorkPhotoResponseDTO:
        """Создание новой записи фотографии работы через DTO."""
        count = await self.repo.count()
        if data.index is None:
            max_index = await self.repo.get_max_index()
            target_index = 0 if count == 0 else max_index + 1
        else:
            target_index = data.index
            await self.repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = WorkPhotoBaseDTO(
            image_url=data.image_url,
            index=target_index,
            is_active=data.is_active,
        )
        new_photo = self.repo.add_photo(base_dto)
        await self.session.flush()

        if data.translations:
            for tr in data.translations:
                self.translation_repo.add_translation(
                    WorkPhotoTranslationInsert(
                        work_photo_id=new_photo.id,
                        locale=tr.locale,
                        title=tr.title,
                        description=tr.description,
                    )
                )
        elif data.title is not None or data.description is not None:
            self.translation_repo.add_translation(
                WorkPhotoTranslationInsert(
                    work_photo_id=new_photo.id,
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
    ) -> WorkPhotoResponseDTO:
        """Загрузка файла, оптимизация в WebP и сохранение новой фотографии работы с переводом."""
        count = await self.repo.count()
        if index is None:
            max_index = await self.repo.get_max_index()
            target_index = 0 if count == 0 else max_index + 1
        else:
            target_index = index
            await self.repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = WorkPhotoBaseDTO(
            image_url="",
            index=target_index,
            is_active=is_active,
        )
        new_photo = self.repo.add_photo(base_dto)
        await self.session.flush()

        file_name = f"img_{uuid.uuid4().hex[:10]}"
        dest = self.path_builder.get_work_photo(
            work_photo_id=new_photo.id, file_name=file_name
        )
        saved_path = await self.image_manager.save_image(file=file, destination=dest)
        media_url = self.image_manager.to_media_url(saved_path)

        new_photo.image_url = media_url

        if title is not None or description is not None:
            self.translation_repo.add_translation(
                WorkPhotoTranslationInsert(
                    work_photo_id=new_photo.id,
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
    ) -> WorkPhotoResponseDTO:
        """Замена файла изображения для существующей фотографии работы."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

        if photo.image_url and self.image_manager:
            self.image_manager.delete_image(photo.image_url)

        file_name = f"img_{uuid.uuid4().hex[:10]}"
        dest = self.path_builder.get_work_photo(
            work_photo_id=photo_id, file_name=file_name
        )
        saved_path = await self.image_manager.save_image(file=file, destination=dest)
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
    ) -> List[WorkPhotoResponseDTO]:
        """Получение списка фотографий работ, отсортированных по index."""
        photos = await self.repo.get_all(
            is_active=is_active,
            skip=skip,
            limit=limit,
        )
        return [self._to_response_dto(p, locale=locale) for p in photos]

    async def get_photo_by_id(
        self, photo_id: int, locale: Optional[Language] = None
    ) -> WorkPhotoResponseDTO:
        """Получение фотографии работы по ID."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")
        return self._to_response_dto(photo, locale=locale)

    async def update_photo(
        self,
        photo_id: int,
        data: Optional[UpdateWorkPhotoRequestDTO] = None,
        file: Optional[UploadFile] = None,
        locale: Optional[Language] = None,
    ) -> WorkPhotoResponseDTO:
        """Обновление атрибутов фотографии работы и/или замена файла."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

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
            dest = self.path_builder.get_work_photo(
                work_photo_id=photo_id, file_name=file_name
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
                    WorkPhotoTranslationInsert(
                        work_photo_id=photo_id,
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
        data: UpdateWorkPhotoIndexRequestDTO,
    ) -> WorkPhotoResponseDTO:
        """Перемещение позиции фотографии работы со сдвигом соседей."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

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
        """Удаление фотографии работы с диска и из БД со сдвигом последующих индексов."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

        has_deps = await self.repo.has_dependencies(photo_id)
        if has_deps:
            raise WorkPhotoHasDependencies(
                f"Cannot delete WorkPhoto {photo_id}: it has dependent records."
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
        self, photo_id: int, data: WorkPhotoTranslationCreate
    ) -> WorkPhotoTranslationResponseDTO:
        """Добавление нового перевода для фотографии работы."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

        existing = await self.translation_repo.get_by_photo_id_and_locale(
            photo_id=photo_id, locale=data.locale
        )
        if existing:
            raise WorkPhotoTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for WorkPhoto {photo_id}."
            )

        new_tr = self.translation_repo.add_translation(
            WorkPhotoTranslationInsert(
                work_photo_id=photo_id,
                locale=data.locale,
                title=data.title,
                description=data.description,
            )
        )
        await self.session.commit()
        await self.session.refresh(new_tr)
        return WorkPhotoTranslationResponseDTO.model_validate(new_tr)

    async def update_translation(
        self, photo_id: int, translation_id: int, data: WorkPhotoTranslationUpdate
    ) -> WorkPhotoTranslationResponseDTO:
        """Обновление существующего перевода фотографии работы."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

        tr = await self.translation_repo.get_by_id(translation_id)
        if not tr or tr.work_photo_id != photo_id:
            raise WorkPhotoTranslationNotFound(
                f"Translation with id {translation_id} not found for WorkPhoto {photo_id}."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("No translation data provided for update.")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()
        await self.session.refresh(tr)
        return WorkPhotoTranslationResponseDTO.model_validate(tr)

    async def delete_translation(self, photo_id: int, translation_id: int) -> None:
        """Удаление перевода фотографии работы. Запрещено удалять единственный перевод."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

        tr = await self.translation_repo.get_by_id(translation_id)
        if not tr or tr.work_photo_id != photo_id:
            raise WorkPhotoTranslationNotFound(
                f"Translation with id {translation_id} not found for WorkPhoto {photo_id}."
            )

        count = await self.translation_repo.count_by_photo_id(photo_id)
        if count <= 1:
            raise WorkPhotoTranslationDeleteError(
                "Cannot delete the only remaining translation for this photo."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()
