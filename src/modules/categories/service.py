from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.categories.exception import (
    CategoryAlreadyExists,
    CategoryHasDependencies,
    CategoryNotFound,
    CategoryTranslationAlreadyExists,
    CategoryTranslationDeleteError,
    CategoryTranslationNotFound,
)
from src.modules.categories.models import Category
from src.modules.categories.models_dto import (
    CategoryBase,
    CategoryCreate,
    CategoryLocalizedResponseDTO,
    CategoryResponseDTO,
    CategoryTranslationCreate,
    CategoryTranslationInsert,
    CategoryTranslationResponseDTO,
    CategoryTranslationUpdate,
    CategoryUpdate,
    CategoryUpdateIndexDTO,
)
from src.modules.categories.repository import (
    CategoryRepository,
    CategoryTranslationRepository,
)
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.service import PathBuilder


class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepository,
        translation_repo: CategoryTranslationRepository,
        session: AsyncSession,
        image_manager: ImageManager,
        path_builder: PathBuilder,
    ):
        self.category_repo = category_repo
        self.translation_repo = translation_repo
        self.session = session
        self.image_manager = image_manager
        self.path_builder = path_builder

    async def create_category(self, data: CategoryCreate) -> CategoryResponseDTO:
        """Создание новой категории товаров с переводами."""
        if not data.translations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one translation is required when creating a Category.",
            )

        existing = await self.category_repo.get_by_slug(data.slug)
        if existing:
            raise CategoryAlreadyExists(f"Category with slug '{data.slug}' already exists.")

        locales = [t.locale for t in data.translations]
        if len(locales) != len(set(locales)):\
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate locales found in translations.",
            )

        if data.index is None:
            max_index = await self.category_repo.get_max_index()
            target_index = max_index + 1
        else:
            target_index = data.index
            await self.category_repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = CategoryBase(
            slug=data.slug,
            image_url=data.image_url,
            index=target_index,
            is_active=data.is_active,
        )
        new_category = await self.category_repo.add_category(base_dto)
        await self.session.flush()

        for trans_data in data.translations:
            insert_dto = CategoryTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                category_id=new_category.id,
            )
            await self.translation_repo.add_translation(insert_dto)

        await self.session.commit()
        created = await self.category_repo.get_by_id(new_category.id)
        dto = CategoryResponseDTO.model_validate(created)
        dto.products_count = 0
        return dto

    async def get_all_categories(
        self,
        locale: Optional[Language] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[CategoryLocalizedResponseDTO]:
        """Получение списка всех категорий с локализованными названиями и количеством товаров."""
        categories = await self.category_repo.get_all(
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

        result: List[CategoryLocalizedResponseDTO] = []
        for cat in categories:
            count = await self.category_repo.get_products_count(cat.id)
            result.append(self._to_localized_dto(cat, locale, count))
        return result

    async def get_category_by_id(self, category_id: int) -> CategoryResponseDTO:
        """Получение категории по ID со всеми переводами."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFound(f"Category with id {category_id} not found.")
        dto = CategoryResponseDTO.model_validate(category)
        dto.products_count = await self.category_repo.get_products_count(category_id)
        return dto

    async def get_category_by_slug(self, slug: str) -> CategoryResponseDTO:
        """Получение категории по slug со всеми переводами."""
        category = await self.category_repo.get_by_slug(slug)
        if not category:
            raise CategoryNotFound(f"Category with slug '{slug}' not found.")
        dto = CategoryResponseDTO.model_validate(category)
        dto.products_count = await self.category_repo.get_products_count(category.id)
        return dto

    async def update_category(
        self,
        category_id: int,
        data: CategoryUpdate,
    ) -> CategoryResponseDTO:
        """Обновление атрибутов категории (slug, image_url, is_active)."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFound(f"Category with id {category_id} not found.")

        if data.slug is not None and data.slug != category.slug:
            existing = await self.category_repo.get_by_slug(data.slug)
            if existing:
                raise CategoryAlreadyExists(f"Category with slug '{data.slug}' already exists.")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.category_repo.update_category(category_id, update_data)
        await self.session.commit()

        updated = await self.category_repo.get_by_id(category_id)
        dto = CategoryResponseDTO.model_validate(updated)
        dto.products_count = await self.category_repo.get_products_count(category_id)
        return dto

    async def reorder_category(
        self,
        category_id: int,
        data: CategoryUpdateIndexDTO,
    ) -> CategoryResponseDTO:
        """Изменение порядкового индекса категории со сдвигом соседей."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFound(f"Category with id {category_id} not found.")

        if category.index != data.new_index:
            await self.category_repo.reorder_index(
                obj_id=category_id,
                old_index=category.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated = await self.category_repo.get_by_id(category_id)
        dto = CategoryResponseDTO.model_validate(updated)
        dto.products_count = await self.category_repo.get_products_count(category_id)
        return dto

    async def delete_category(self, category_id: int) -> None:
        """Удаление категории с проверкой связанных товаров."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFound(f"Category with id {category_id} not found.")

        has_deps = await self.category_repo.has_dependencies(category_id)
        if has_deps:
            raise CategoryHasDependencies(
                f"Cannot delete Category with id {category_id} because it is referenced by products."
            )

        if category.image_url and self.image_manager:
            self.image_manager.delete_image(category.image_url)

        await self.category_repo.delete_category(category_id)
        await self.category_repo.shift_indexes_after_delete(category.index)
        await self.session.commit()

    async def upload_image(
        self,
        category_id: int,
        file: UploadFile,
    ) -> CategoryResponseDTO:
        """Загрузка, оптимизация и сохранение изображения категории."""

        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFound(f"Category with id {category_id} not found.")

        if category.image_url:
            self.image_manager.delete_image(category.image_url)

        dest = self.path_builder.get_category(category_id=category_id, file_name="image")
        saved_path = await self.image_manager.save_image(file=file, destination=dest)
        media_url = self.image_manager.to_media_url(saved_path)

        await self.category_repo.update_category(category_id, {"image_url": media_url})
        await self.session.commit()

        updated = await self.category_repo.get_by_id(category_id)
        dto = CategoryResponseDTO.model_validate(updated)
        dto.products_count = await self.category_repo.get_products_count(category_id)
        return dto

    async def delete_image(self, category_id: int) -> CategoryResponseDTO:
        """Удаление изображения категории."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFound(f"Category with id {category_id} not found.")

        if category.image_url and self.image_manager:
            self.image_manager.delete_image(category.image_url)

        await self.category_repo.update_category(category_id, {"image_url": None})
        await self.session.commit()

        updated = await self.category_repo.get_by_id(category_id)
        dto = CategoryResponseDTO.model_validate(updated)
        dto.products_count = await self.category_repo.get_products_count(category_id)
        return dto

    async def create_translation(
        self,
        category_id: int,
        data: CategoryTranslationCreate,
    ) -> CategoryTranslationResponseDTO:
        """Добавление перевода для категории."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFound(f"Category with id {category_id} not found.")

        existing = await self.translation_repo.get_by_category_and_locale(
            category_id=category_id,
            locale=data.locale,
        )
        if existing:
            raise CategoryTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for category {category_id}."
            )

        insert_dto = CategoryTranslationInsert(
            locale=data.locale,
            name=data.name,
            category_id=category_id,
        )
        trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        return CategoryTranslationResponseDTO.model_validate(trans)

    async def update_translation(
        self,
        translation_id: int,
        data: CategoryTranslationUpdate,
    ) -> CategoryTranslationResponseDTO:
        """Обновление перевода категории."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise CategoryTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()

        updated = await self.translation_repo.get_by_id(translation_id)
        return CategoryTranslationResponseDTO.model_validate(updated)

    async def delete_translation(
        self,
        translation_id: int,
    ) -> None:
        """Удаление перевода категории (с запретом удаления последнего)."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise CategoryTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        category = await self.category_repo.get_by_id(trans.category_id)
        if not category or len(category.translations) <= 1:
            raise CategoryTranslationDeleteError(
                "Cannot delete the only remaining translation of the category."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()

    def _to_localized_dto(
        self,
        category: Category,
        locale: Optional[Language],
        products_count: int = 0,
    ) -> CategoryLocalizedResponseDTO:
        """Конвертация в локализованное DTO с fallback-логикой."""
        target_locale = locale or Language.ENG
        name = category._get_field_with_translation(
            lambda t: t.name,
            target_locale,
            fallback=Language.GER,
        )

        return CategoryLocalizedResponseDTO(
            id=category.id,
            slug=category.slug,
            image_url=category.image_url,
            index=category.index,
            is_active=category.is_active,
            name=name if name else "No Translation",
            products_count=products_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
