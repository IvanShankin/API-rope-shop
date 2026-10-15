from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.product_application.exception import (
    ProductApplicationAlreadyExists,
    ProductApplicationHasDependencies,
    ProductApplicationNotFound,
    ProductApplicationTranslationAlreadyExists,
    ProductApplicationTranslationDeleteError,
    ProductApplicationTranslationNotFound,
    ProductAssignedApplicationAlreadyExists,
    ProductAssignedApplicationNotFound,
)
from src.modules.product_application.models import ProductApplication
from src.modules.product_application.models_dto import (
    AssignApplicationToProductDTO,
    ProductApplicationCreate,
    ProductApplicationLocalizedResponseDTO,
    ProductApplicationResponseDTO,
    ProductApplicationTranslationCreate,
    ProductApplicationTranslationInsert,
    ProductApplicationTranslationResponseDTO,
    ProductApplicationTranslationUpdate,
    ProductApplicationUpdate,
    ProductApplicationUpdateIndexDTO,
    ProductAssignedApplicationResponseDTO,
)
from src.modules.product_application.repository import (
    ProductApplicationRepository,
    ProductApplicationTranslationRepository,
    ProductAssignedApplicationRepository,
)
from src.modules.products.exception import ProductNotFound
from src.modules.products.repository import ProductRepository


class ProductApplicationService:
    def __init__(
        self,
        app_repo: ProductApplicationRepository,
        trans_repo: ProductApplicationTranslationRepository,
        assigned_repo: ProductAssignedApplicationRepository,
        product_repo: ProductRepository,
        session_db: AsyncSession,
    ):
        self.app_repo = app_repo
        self.trans_repo = trans_repo
        self.assigned_repo = assigned_repo
        self.product_repo = product_repo
        self.session_db = session_db

    # ==================== Application CRUD ====================\

    async def get_all_applications(
        self,
        locale: Optional[Language] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Union[List[ProductApplicationLocalizedResponseDTO], List[ProductApplicationResponseDTO]]:
        """Получение списка всех назначений (локализованных или со всеми переводами)."""
        apps = await self.app_repo.get_all(is_active=is_active, skip=skip, limit=limit)

        if locale is not None:
            result_localized: List[ProductApplicationLocalizedResponseDTO] = []
            for app in apps:
                name = app._get_field_with_translation(lambda t: t.name, locale) or ""
                result_localized.append(
                    ProductApplicationLocalizedResponseDTO(
                        id=app.id,
                        code=app.code,
                        index=app.index,
                        is_active=app.is_active,
                        name=name,
                    )
                )
            return result_localized

        return [ProductApplicationResponseDTO.model_validate(app) for app in apps]

    async def get_application_by_id(self, app_id: int) -> ProductApplicationResponseDTO:
        """Получение назначения по ID."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {app_id} not found.")
        return ProductApplicationResponseDTO.model_validate(app)

    async def get_application_by_code(self, code: str) -> ProductApplicationResponseDTO:
        """Получение назначения по коду."""
        app = await self.app_repo.get_by_code(code)
        if not app:
            raise ProductApplicationNotFound(f"Application with code '{code}' not found.")
        return ProductApplicationResponseDTO.model_validate(app)

    async def create_application(self, data: ProductApplicationCreate) -> ProductApplicationResponseDTO:
        """Создание нового назначения."""
        if await self.app_repo.exists_code(data.code):
            raise ProductApplicationAlreadyExists(f"Application with code '{data.code}' already exists.")

        locales = [t.locale for t in data.translations]
        if len(locales) != len(set(locales)):
            raise ProductApplicationTranslationAlreadyExists(
                "Duplicate locales found in translations."
            )

        if data.index is None:
            max_index = await self.app_repo.get_max_index()
            apps_count = await self.app_repo.count()
            target_index = max_index + 1 if apps_count > 0 else 0
        else:
            target_index = data.index
            await self.app_repo.shift_indexes_for_insert(target_index=target_index)

        app = await self.app_repo.add_application(
            code=data.code,
            index=target_index,
            is_active=data.is_active,
        )
        await self.session_db.flush()

        for t in data.translations:
            insert_dto = ProductApplicationTranslationInsert(
                application_id=app.id,
                locale=t.locale,
                name=t.name,
            )
            await self.trans_repo.add_translation(insert_dto)

        await self.session_db.commit()
        created = await self.app_repo.get_by_id(app.id)
        return ProductApplicationResponseDTO.model_validate(created)

    async def update_application(self, app_id: int, data: ProductApplicationUpdate) -> ProductApplicationResponseDTO:
        """Обновление атрибутов назначения."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {app_id} not found.")

        if data.code is not None and data.code != app.code:
            existing = await self.app_repo.get_by_code(data.code)
            if existing:
                raise ProductApplicationAlreadyExists(f"Application with code '{data.code}' already exists.")

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("Did not transmit data")

        await self.app_repo.update_application(app_id, update_dict)
        await self.session_db.commit()
        updated = await self.app_repo.get_by_id(app_id)
        return ProductApplicationResponseDTO.model_validate(updated)

    async def reorder_application(
        self, app_id: int, data: ProductApplicationUpdateIndexDTO
    ) -> ProductApplicationResponseDTO:
        """Изменение порядка назначения со сдвигом соседей."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {app_id} not found.")

        if app.index != data.new_index:
            await self.app_repo.reorder_index(
                obj_id=app.id,
                old_index=app.index,
                new_index=data.new_index,
            )
            await self.session_db.commit()

        updated = await self.app_repo.get_by_id(app_id)
        return ProductApplicationResponseDTO.model_validate(updated)

    async def delete_application(self, app_id: int) -> None:
        """Удаление назначения со сдвигом индексов."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {app_id} not found.")

        if await self.app_repo.has_dependencies(app_id):
            raise ProductApplicationHasDependencies(
                f"Cannot delete application with id {app_id} because it is assigned to products."
            )

        deleted_index = app.index
        await self.app_repo.delete_application(app_id)
        await self.app_repo.shift_indexes_after_delete(deleted_index=deleted_index)
        await self.session_db.commit()

    # ==================== Translation Operations ====================

    async def add_translation(
        self, app_id: int, data: ProductApplicationTranslationCreate
    ) -> ProductApplicationTranslationResponseDTO:
        """Добавление перевода для назначения."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {app_id} not found.")

        existing = await self.trans_repo.get_by_application_and_locale(app_id, data.locale)
        if existing:
            raise ProductApplicationTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for application {app_id}."
            )

        insert_dto = ProductApplicationTranslationInsert(
            application_id=app_id,
            locale=data.locale,
            name=data.name,
        )
        translation = await self.trans_repo.add_translation(insert_dto)
        await self.session_db.commit()
        await self.session_db.refresh(translation)
        return ProductApplicationTranslationResponseDTO.model_validate(translation)

    async def update_translation(
        self, app_id: int, locale: Language, data: ProductApplicationTranslationUpdate
    ) -> ProductApplicationTranslationResponseDTO:
        """Обновление перевода по локали."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {app_id} not found.")

        translation = await self.trans_repo.get_by_application_and_locale(app_id, locale)
        if not translation:
            raise ProductApplicationTranslationNotFound(
                f"Translation for application {app_id} with locale {locale.value} not found."
            )

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("Did not transmit data")

        await self.trans_repo.update_translation(translation.id, update_dict)
        await self.session_db.commit()
        updated = await self.trans_repo.get_by_application_and_locale(app_id, locale)
        return ProductApplicationTranslationResponseDTO.model_validate(updated)

    async def delete_translation(self, app_id: int, locale: Language) -> None:
        """Удаление перевода по локали (нельзя удалять последний перевод)."""
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {app_id} not found.")

        translation = await self.trans_repo.get_by_application_and_locale(app_id, locale)
        if not translation:
            raise ProductApplicationTranslationNotFound(
                f"Translation for application {app_id} with locale {locale.value} not found."
            )

        if len(app.translations) <= 1:
            raise ProductApplicationTranslationDeleteError(
                "Cannot delete the last translation of an application."
            )

        await self.trans_repo.delete_translation(translation.id)
        await self.session_db.commit()

    # ==================== Product Assignment ====================

    async def assign_to_product(
        self,
        product_id: int,
        data: AssignApplicationToProductDTO,
        locale: Optional[Language] = None,
    ) -> ProductAssignedApplicationResponseDTO:
        """Привязка назначения к товару."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        app = await self.app_repo.get_by_id(data.application_id)
        if not app:
            raise ProductApplicationNotFound(f"Application with id {data.application_id} not found.")

        if await self.assigned_repo.exists_assignment(product_id, data.application_id):
            raise ProductAssignedApplicationAlreadyExists(
                f"Application {data.application_id} is already assigned to product {product_id}."
            )

        target_locale = locale or Language.ENG
        name = app._get_field_with_translation(lambda t: t.name, target_locale) or ""
        localized_app = ProductApplicationLocalizedResponseDTO(
            id=app.id,
            code=app.code,
            index=app.index,
            is_active=app.is_active,
            name=name,
        )

        await self.assigned_repo.assign_application(product_id, data.application_id)
        await self.session_db.commit()

        return ProductAssignedApplicationResponseDTO(
            product_id=product_id,
            application_id=data.application_id,
            application=localized_app,
        )

    async def unassign_from_product(self, product_id: int, application_id: int) -> None:
        """Отвязка назначения от товара."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        if not await self.assigned_repo.exists_assignment(product_id, application_id):
            raise ProductAssignedApplicationNotFound(
                f"Application {application_id} is not assigned to product {product_id}."
            )

        await self.assigned_repo.unassign_application(product_id, application_id)
        await self.session_db.commit()

    async def get_product_applications(
        self, product_id: int, locale: Optional[Language] = None
    ) -> List[ProductApplicationLocalizedResponseDTO]:
        """Получение списка назначений конкретного товара."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        assignments = await self.assigned_repo.get_by_product_id(product_id)
        target_locale = locale or Language.ENG

        result: List[ProductApplicationLocalizedResponseDTO] = []
        for a in assignments:
            if a.application:
                name = a.application._get_field_with_translation(lambda t: t.name, target_locale) or ""
                result.append(
                    ProductApplicationLocalizedResponseDTO(
                        id=a.application.id,
                        code=a.application.code,
                        index=a.application.index,
                        is_active=a.application.is_active,
                        name=name,
                    )
                )
        return result
