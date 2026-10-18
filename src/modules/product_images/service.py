import uuid
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NoDataForUpdate
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.service import PathBuilder
from src.modules.product_images.exception import (
    ProductImageHasDependencies,
    ProductImageNotFound,
)
from src.modules.product_images.models_dto import (
    ProductImageBase,
    ProductImageCreate,
    ProductImageResponseDTO,
    ProductImageUpdate,
    ProductImageUpdateIndexDTO,
)
from src.modules.product_images.repository import ProductImageRepository
from src.modules.products.exception import ProductNotFound
from src.modules.products.repository import ProductRepository


class ProductImageService:
    def __init__(
        self,
        repo: ProductImageRepository,
        product_repo: ProductRepository,
        session: AsyncSession,
        image_manager: ImageManager,
        path_builder: PathBuilder,
    ):
        self.repo = repo
        self.product_repo = product_repo
        self.session = session
        self.image_manager = image_manager
        self.path_builder = path_builder

    async def create_image(self, data: ProductImageCreate) -> ProductImageResponseDTO:
        """Создание новой записи изображения товара через DTO."""
        product = await self.product_repo.get_by_id(data.product_id)
        if not product:
            raise ProductNotFound(f"Product with id {data.product_id} not found.")

        count = await self.repo.count_by_product_id(data.product_id)
        is_main = True if count == 0 else data.is_main

        if is_main:
            await self.repo.reset_main_images(product_id=data.product_id)

        if data.index is None:
            max_index = await self.repo.get_max_index(product_id=data.product_id)
            target_index = max_index + 1
        else:
            target_index = data.index
            await self.repo.shift_indexes_for_insert(
                target_index=target_index,
                product_id=data.product_id,
            )

        base_dto = ProductImageBase(
            product_id=data.product_id,
            image_url=data.image_url,
            is_main=is_main,
            index=target_index,
            is_active=data.is_active,
        )
        new_image = self.repo.add_image(base_dto)
        await self.session.commit()

        loaded = await self.repo.get_by_id(new_image.id)
        return ProductImageResponseDTO.model_validate(loaded)

    async def upload_image(
        self,
        product_id: int,
        file: UploadFile,
        is_main: bool = False,
        index: Optional[int] = None,
        is_active: bool = True,
    ) -> ProductImageResponseDTO:
        """Загрузка файла, оптимизация в WebP и сохранение записи изображения."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        file_name = f"img_{uuid.uuid4().hex[:10]}"
        dest = self.path_builder.get_product(product_id=product_id, file_name=file_name)
        saved_path = await self.image_manager.save_image(file=file, destination=dest)
        media_url = self.image_manager.to_media_url(saved_path)

        create_dto = ProductImageCreate(
            product_id=product_id,
            image_url=media_url,
            is_main=is_main,
            index=index,
            is_active=is_active,
        )
        return await self.create_image(create_dto)

    async def get_images_by_product(
        self,
        product_id: int,
        is_active: Optional[bool] = None,
    ) -> List[ProductImageResponseDTO]:
        """Получение списка всех изображений товара, отсортированных по index."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        images = await self.repo.get_by_product_id(product_id=product_id, is_active=is_active)
        return [ProductImageResponseDTO.model_validate(img) for img in images]

    async def get_image_by_id(self, image_id: int) -> ProductImageResponseDTO:
        """Получение изображения товара по ID."""
        image = await self.repo.get_by_id(image_id)
        if not image:
            raise ProductImageNotFound(f"ProductImage with id {image_id} not found.")
        return ProductImageResponseDTO.model_validate(image)

    async def update_image(
        self,
        image_id: int,
        data: ProductImageUpdate,
    ) -> ProductImageResponseDTO:
        """Обновление атрибутов изображения."""
        image = await self.repo.get_by_id(image_id)
        if not image:
            raise ProductImageNotFound(f"ProductImage with id {image_id} not found.")

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("No data provided for update.")

        if data.is_main:
            await self.repo.reset_main_images(
                product_id=image.product_id,
                exclude_image_id=image_id,
            )

        await self.repo.update_image(image_id=image_id, update_data=update_dict)
        await self.session.commit()

        updated = await self.repo.get_by_id(image_id)
        return ProductImageResponseDTO.model_validate(updated)

    async def set_main_image(self, image_id: int) -> ProductImageResponseDTO:
        """Установка изображения в качестве главного для своего товара."""
        image = await self.repo.get_by_id(image_id)
        if not image:
            raise ProductImageNotFound(f"ProductImage with id {image_id} not found.")

        await self.repo.reset_main_images(
            product_id=image.product_id,
            exclude_image_id=image_id,
        )
        await self.repo.update_image(image_id=image_id, update_data={"is_main": True})
        await self.session.commit()

        updated = await self.repo.get_by_id(image_id)
        return ProductImageResponseDTO.model_validate(updated)

    async def reorder_image(
        self,
        image_id: int,
        data: ProductImageUpdateIndexDTO,
    ) -> ProductImageResponseDTO:
        """Перемещение позиции изображения товара со сдвигом соседних."""
        image = await self.repo.get_by_id(image_id)
        if not image:
            raise ProductImageNotFound(f"ProductImage with id {image_id} not found.")

        if image.index != data.new_index:
            await self.repo.reorder_index(
                obj_id=image_id,
                old_index=image.index,
                new_index=data.new_index,
                product_id=image.product_id,
            )
            await self.session.commit()

        updated = await self.repo.get_by_id(image_id)
        return ProductImageResponseDTO.model_validate(updated)

    async def delete_image(self, image_id: int) -> None:
        """Удаление изображения с диска и из БД."""
        image = await self.repo.get_by_id(image_id)
        if not image:
            raise ProductImageNotFound(f"ProductImage with id {image_id} not found.")

        has_deps = await self.repo.has_dependencies(image_id)
        if has_deps:
            raise ProductImageHasDependencies(
                f"Cannot delete ProductImage {image_id}: it has dependent records."
            )

        deleted_index = image.index
        product_id = image.product_id
        was_main = image.is_main
        image_url = image.image_url

        if image_url and self.image_manager:
            self.image_manager.delete_image(image_url)

        await self.repo.delete_image(image_id)
        await self.repo.shift_indexes_after_delete(
            deleted_index=deleted_index,
            product_id=product_id,
        )

        if was_main:
            remaining = await self.repo.get_by_product_id(product_id)
            if remaining:
                await self.repo.update_image(remaining[0].id, {"is_main": True})

        await self.session.commit()
