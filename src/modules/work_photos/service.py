import uuid
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NoDataForUpdate
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.service import PathBuilder
from src.modules.work_photos.exception import (
    WorkPhotoHasDependencies,
    WorkPhotoNotFound,
)
from src.modules.work_photos.models_dto import (
    CreateWorkPhotoRequestDTO,
    UpdateWorkPhotoIndexRequestDTO,
    UpdateWorkPhotoRequestDTO,
    WorkPhotoBaseDTO,
    WorkPhotoResponseDTO,
)
from src.modules.work_photos.repository import WorkPhotoRepository


class WorkPhotoService:
    def __init__(
        self,
        repo: WorkPhotoRepository,
        session: AsyncSession,
        image_manager: ImageManager,
        path_builder: PathBuilder,
    ):
        self.repo = repo
        self.session = session
        self.image_manager = image_manager
        self.path_builder = path_builder

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
            title=data.title,
            description=data.description,
            index=target_index,
            is_active=data.is_active,
        )
        new_photo = self.repo.add_photo(base_dto)
        await self.session.commit()

        loaded = await self.repo.get_by_id(new_photo.id)
        return WorkPhotoResponseDTO.model_validate(loaded)

    async def upload_photo(
        self,
        file: UploadFile,
        title: Optional[str] = None,
        description: Optional[str] = None,
        index: Optional[int] = None,
        is_active: bool = True,
    ) -> WorkPhotoResponseDTO:
        """Загрузка файла, оптимизация в WebP и сохранение новой фотографии работы."""
        count = await self.repo.count()
        if index is None:
            max_index = await self.repo.get_max_index()
            target_index = 0 if count == 0 else max_index + 1
        else:
            target_index = index
            await self.repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = WorkPhotoBaseDTO(
            image_url="",
            title=title,
            description=description,
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
        await self.session.commit()

        loaded = await self.repo.get_by_id(new_photo.id)
        return WorkPhotoResponseDTO.model_validate(loaded)

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
        return WorkPhotoResponseDTO.model_validate(loaded)

    async def get_photos(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[WorkPhotoResponseDTO]:
        """Получение списка фотографий работ, отсортированных по index."""
        photos = await self.repo.get_all(
            is_active=is_active,
            skip=skip,
            limit=limit,
        )
        return [WorkPhotoResponseDTO.model_validate(p) for p in photos]

    async def get_photo_by_id(self, photo_id: int) -> WorkPhotoResponseDTO:
        """Получение фотографии работы по ID."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")
        return WorkPhotoResponseDTO.model_validate(photo)

    async def update_photo(
        self,
        photo_id: int,
        data: Optional[UpdateWorkPhotoRequestDTO] = None,
        file: Optional[UploadFile] = None,
    ) -> WorkPhotoResponseDTO:
        """Обновление атрибутов фотографии работы и/или замена файла."""
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise WorkPhotoNotFound(f"WorkPhoto with id {photo_id} not found.")

        update_dict = data.model_dump(exclude_unset=True) if data else {}
        update_dict = {k: v for k, v in update_dict.items() if v is not None}

        if not update_dict and file is None:
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
            await self.session.commit()

        updated = await self.repo.get_by_id(photo_id)
        return WorkPhotoResponseDTO.model_validate(updated)

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
        return WorkPhotoResponseDTO.model_validate(updated)

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
