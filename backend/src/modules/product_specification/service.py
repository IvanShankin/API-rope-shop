from typing import List, Optional, Union, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.products.exception import ProductNotFound

if TYPE_CHECKING:
    from src.modules.products.repository import ProductRepository
from src.modules.product_specification.exception import (
    ProductSpecificationNotFound,
    ProductSpecificationTranslationDeleteError,
    ProductSpecificationTranslationNotFound,
)
from src.modules.product_specification.models import ProductSpecification
from src.modules.product_specification.models_dto import (
    ProductSpecificationBatchCreate,
    ProductSpecificationBatchDelete,
    ProductSpecificationBatchDeleteResponseDTO,
    ProductSpecificationBatchSync,
    ProductSpecificationBatchUpdate,
    ProductSpecificationCreate,
    ProductSpecificationLocalizedResponseDTO,
    ProductSpecificationResponseDTO,
    ProductSpecificationTranslationCreate,
    ProductSpecificationTranslationResponseDTO,
    ProductSpecificationTranslationUpdate,
    ProductSpecificationUpdate,
    ProductSpecificationUpdateIndexDTO,
)
from src.modules.product_specification.repository import (
    ProductSpecificationRepository,
    ProductSpecificationTranslationRepository,
)


class ProductSpecificationService:
    def __init__(
        self,
        spec_repo: ProductSpecificationRepository,
        trans_repo: ProductSpecificationTranslationRepository,
        product_repo: "ProductRepository",
        session_db: AsyncSession,
    ):
        self.spec_repo = spec_repo
        self.trans_repo = trans_repo
        self.product_repo = product_repo
        self.session_db = session_db

    async def _validate_product_exists(self, product_id: int) -> None:
        """Проверка существования товара."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

    # ==================== Batch Operations ====================

    async def create_batch(
        self, product_id: int, data: ProductSpecificationBatchCreate
    ) -> List[ProductSpecificationResponseDTO]:
        """Пакетное создание характеристик для товара."""
        await self._validate_product_exists(product_id)

        max_index = await self.spec_repo.get_max_index(product_id=product_id)
        current_count = await self.spec_repo.count_by_product_id(product_id)
        next_index = max_index + 1 if current_count > 0 else 0

        created_specs: List[ProductSpecification] = []
        for item in data.items:
            target_index = item.index if item.index is not None else next_index
            if item.index is None:
                next_index += 1

            spec = await self.spec_repo.add_specification(
                product_id=product_id,
                index=target_index,
            )
            await self.session_db.flush()

            for t in item.translations:
                await self.trans_repo.add_translation(
                    {
                        "specification_id": spec.id,
                        "locale": t.locale,
                        "name": t.name,
                        "value": t.value,
                    }
                )
            created_specs.append(spec)

        await self.session_db.commit()

        # Загружаем с предзагрузкой переводов
        for s in created_specs:
            await self.session_db.refresh(s, ["translations"])

        return [ProductSpecificationResponseDTO.model_validate(s) for s in created_specs]

    async def update_batch(
        self, product_id: int, data: ProductSpecificationBatchUpdate
    ) -> List[ProductSpecificationResponseDTO]:
        """Пакетное обновление характеристик конкретного товара."""
        await self._validate_product_exists(product_id)

        spec_ids = [item.id for item in data.items]
        existing_specs = await self.spec_repo.get_by_ids_and_product(spec_ids, product_id)
        found_ids = {s.id for s in existing_specs}
        missing_ids = set(spec_ids) - found_ids

        if missing_ids:
            raise ProductSpecificationNotFound(
                f"Specifications {missing_ids} not found for product {product_id}."
            )

        for item in data.items:
            if item.index is not None:
                await self.spec_repo.update_specification(
                    item.id,
                    {"index": item.index},
                )

            if item.translations:
                for t in item.translations:
                    await self.trans_repo.upsert_translation(
                        spec_id=item.id,
                        locale=t.locale,
                        name=t.name,
                        value=t.value,
                    )

        await self.session_db.commit()

        for s in existing_specs:
            await self.session_db.refresh(s, ["translations"])

        return [ProductSpecificationResponseDTO.model_validate(s) for s in existing_specs]

    async def delete_batch(
        self, product_id: int, data: ProductSpecificationBatchDelete
    ) -> ProductSpecificationBatchDeleteResponseDTO:
        """Пакетное удаление характеристик конкретного товара."""
        await self._validate_product_exists(product_id)

        existing_specs = await self.spec_repo.get_by_ids_and_product(
            data.specification_ids, product_id
        )
        found_ids = [s.id for s in existing_specs]

        if not found_ids:
            raise ProductSpecificationNotFound(
                f"No matching specifications found for product {product_id}."
            )

        deleted_count = await self.spec_repo.delete_by_ids_and_product(found_ids, product_id)

        # Выравниваем оставшиеся индексы
        remaining = await self.spec_repo.get_by_product_id(product_id)
        for idx, s in enumerate(remaining):
            if s.index != idx:
                await self.spec_repo.update_specification(s.id, {"index": idx})

        await self.session_db.commit()
        return ProductSpecificationBatchDeleteResponseDTO(
            deleted_count=deleted_count,
            deleted_ids=found_ids,
        )

    async def sync_batch(
        self, product_id: int, data: ProductSpecificationBatchSync
    ) -> List[ProductSpecificationResponseDTO]:
        """
        Полная синхронизация (замена/сохранение всего списка) характеристик товара.
        - Удаляет отсутствующие в переданном списке характеристики.
        - Обновляет существующие (с указанным ID).
        - Создает новые (без ID или с несуществующим ID).
        - Пересчитывает порядок `index`.
        """
        await self._validate_product_exists(product_id)

        existing_specs = await self.spec_repo.get_by_product_id(product_id)
        existing_map = {s.id: s for s in existing_specs}

        requested_ids = {item.id for item in data.items if item.id is not None}
        to_delete_ids = [s_id for s_id in existing_map if s_id not in requested_ids]

        if to_delete_ids:
            await self.spec_repo.delete_by_ids_and_product(to_delete_ids, product_id)

        persisted_specs: List[ProductSpecification] = []
        for idx, item in enumerate(data.items):
            target_index = item.index if item.index is not None else idx

            if item.id and item.id in existing_map:
                # Обновление существующей
                spec = existing_map[item.id]
                await self.spec_repo.update_specification(item.id, {"index": target_index})
                for t in item.translations:
                    await self.trans_repo.upsert_translation(
                        spec_id=item.id,
                        locale=t.locale,
                        name=t.name,
                        value=t.value,
                    )
                persisted_specs.append(spec)
            else:
                # Создание новой
                new_spec = await self.spec_repo.add_specification(
                    product_id=product_id,
                    index=target_index,
                )
                await self.session_db.flush()
                for t in item.translations:
                    await self.trans_repo.add_translation(
                        {
                            "specification_id": new_spec.id,
                            "locale": t.locale,
                            "name": t.name,
                            "value": t.value,
                        }
                    )
                persisted_specs.append(new_spec)

        await self.session_db.commit()

        for s in persisted_specs:
            await self.session_db.refresh(s, ["translations"])

        return [ProductSpecificationResponseDTO.model_validate(s) for s in persisted_specs]

    # ==================== Read Operations ====================

    async def get_by_product_id(
        self, product_id: int, locale: Optional[Language] = None
    ) -> List[ProductSpecificationResponseDTO]:
        """Получение всех характеристик товара (с локализацией или с полным списком переводов)."""
        await self._validate_product_exists(product_id)
        specs = await self.spec_repo.get_by_product_id(product_id)

        if locale is not None:
            result_localized: List[ProductSpecificationResponseDTO] = []
            for s in specs:
                name = s._get_field_with_translation(lambda t: t.name, locale) or ""
                value = s._get_field_with_translation(lambda t: t.value, locale) or ""
                result_localized.append(
                    ProductSpecificationResponseDTO(
                        id=s.id,
                        product_id=s.product_id,
                        index=s.index,
                        name=name,
                        value=value,
                        translations=[],
                    )
                )
            return result_localized

        return [ProductSpecificationResponseDTO.model_validate(s) for s in specs]

    async def get_by_id(self, spec_id: int) -> ProductSpecificationResponseDTO:
        """Получение характеристики по ID."""
        spec = await self.spec_repo.get_by_id(spec_id)
        if not spec:
            raise ProductSpecificationNotFound(f"Specification with id {spec_id} not found.")
        return ProductSpecificationResponseDTO.model_validate(spec)

    # ==================== Single CRUD Operations ====================

    async def create_specification(
        self, data: ProductSpecificationCreate
    ) -> ProductSpecificationResponseDTO:
        """Создание одной характеристики."""
        await self._validate_product_exists(data.product_id)

        if data.index is None:
            max_index = await self.spec_repo.get_max_index(product_id=data.product_id)
            count = await self.spec_repo.count_by_product_id(data.product_id)
            target_index = max_index + 1 if count > 0 else 0
        else:
            target_index = data.index
            await self.spec_repo.shift_indexes_for_insert(
                target_index=target_index,
                product_id=data.product_id,
            )

        spec = await self.spec_repo.add_specification(
            product_id=data.product_id,
            index=target_index,
        )
        await self.session_db.flush()

        for t in data.translations:
            await self.trans_repo.add_translation(
                {
                    "specification_id": spec.id,
                    "locale": t.locale,
                    "name": t.name,
                    "value": t.value,
                }
            )

        await self.session_db.commit()
        await self.session_db.refresh(spec, ["translations"])
        return ProductSpecificationResponseDTO.model_validate(spec)

    async def update_specification(
        self, spec_id: int, data: ProductSpecificationUpdate
    ) -> ProductSpecificationResponseDTO:
        """Обновление характеристики (индекс и/или переводы)."""
        spec = await self.spec_repo.get_by_id(spec_id)
        if not spec:
            raise ProductSpecificationNotFound(f"Specification with id {spec_id} not found.")

        if data.index is not None and data.index != spec.index:
            await self.spec_repo.reorder_index(
                obj_id=spec.id,
                old_index=spec.index,
                new_index=data.index,
                product_id=spec.product_id,
            )

        if data.translations:
            for t in data.translations:
                await self.trans_repo.upsert_translation(
                    spec_id=spec.id,
                    locale=t.locale,
                    name=t.name,
                    value=t.value,
                )

        await self.session_db.commit()
        await self.session_db.refresh(spec, ["translations"])
        return ProductSpecificationResponseDTO.model_validate(spec)

    async def reorder_specification(
        self, spec_id: int, data: ProductSpecificationUpdateIndexDTO
    ) -> ProductSpecificationResponseDTO:
        """Изменение порядка характеристики в рамках товара."""
        spec = await self.spec_repo.get_by_id(spec_id)
        if not spec:
            raise ProductSpecificationNotFound(f"Specification with id {spec_id} not found.")

        await self.spec_repo.reorder_index(
            obj_id=spec.id,
            old_index=spec.index,
            new_index=data.new_index,
            product_id=spec.product_id,
        )
        await self.session_db.commit()
        await self.session_db.refresh(spec, ["translations"])
        return ProductSpecificationResponseDTO.model_validate(spec)

    async def delete_specification(self, spec_id: int) -> None:
        """Удаление характеристики со сдвигом индексов."""
        spec = await self.spec_repo.get_by_id(spec_id)
        if not spec:
            raise ProductSpecificationNotFound(f"Specification with id {spec_id} not found.")

        deleted_index = spec.index
        product_id = spec.product_id

        await self.spec_repo.delete_specification(spec_id)
        await self.spec_repo.shift_indexes_after_delete(
            deleted_index=deleted_index,
            product_id=product_id,
        )
        await self.session_db.commit()

    async def delete_all_by_product(self, product_id: int) -> int:
        """Удаление всех характеристик товара."""
        await self._validate_product_exists(product_id)
        deleted_count = await self.spec_repo.delete_by_product_id(product_id)
        await self.session_db.commit()
        return deleted_count

    # ==================== Translation Operations ====================

    async def add_translation(
        self, spec_id: int, data: ProductSpecificationTranslationCreate
    ) -> ProductSpecificationTranslationResponseDTO:
        """Добавление перевода для характеристики."""
        spec = await self.spec_repo.get_by_id(spec_id)
        if not spec:
            raise ProductSpecificationNotFound(f"Specification with id {spec_id} not found.")

        existing = await self.trans_repo.get_by_specification_and_locale(spec_id, data.locale)
        if existing:
            existing.name = data.name
            existing.value = data.value
            await self.session_db.commit()
            await self.session_db.refresh(existing)
            return ProductSpecificationTranslationResponseDTO.model_validate(existing)

        translation = await self.trans_repo.add_translation(
            {
                "specification_id": spec_id,
                "locale": data.locale,
                "name": data.name,
                "value": data.value,
            }
        )
        await self.session_db.commit()
        await self.session_db.refresh(translation)
        return ProductSpecificationTranslationResponseDTO.model_validate(translation)

    async def update_translation(
        self, spec_id: int, locale: Language, data: ProductSpecificationTranslationUpdate
    ) -> ProductSpecificationTranslationResponseDTO:
        """Обновление перевода характеристики."""
        translation = await self.trans_repo.get_by_specification_and_locale(spec_id, locale)
        if not translation:
            raise ProductSpecificationTranslationNotFound(
                f"Translation for specification {spec_id} with locale {locale.value} not found."
            )

        update_dict = data.model_dump(exclude_unset=True)
        if update_dict:
            await self.trans_repo.update_translation(translation.id, update_dict)
            await self.session_db.commit()
            await self.session_db.refresh(translation)

        return ProductSpecificationTranslationResponseDTO.model_validate(translation)

    async def delete_translation(self, spec_id: int, locale: Language) -> None:
        """Удаление перевода характеристики (запрещено удалять последний перевод)."""
        translation = await self.trans_repo.get_by_specification_and_locale(spec_id, locale)
        if not translation:
            raise ProductSpecificationTranslationNotFound(
                f"Translation for specification {spec_id} with locale {locale.value} not found."
            )

        count = await self.trans_repo.count_by_specification_id(spec_id)
        if count <= 1:
            raise ProductSpecificationTranslationDeleteError(
                "Cannot delete the last translation of a specification."
            )

        await self.trans_repo.delete_translation(translation.id)
        await self.session_db.commit()
