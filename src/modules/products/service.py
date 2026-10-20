import shutil
from typing import List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.categories.repository import CategoryRepository
from src.modules.colors.models_dto import ColorLocalizedResponseDTO
from src.modules.product_application.models_dto import ProductApplicationLocalizedResponseDTO
from src.modules.product_images.models_dto import ProductImageResponseDTO
from src.modules.product_specification.models_dto import ProductSpecificationLocalizedResponseDTO
from src.modules.products.exception import (
    ProductAlreadyExists,
    ProductCategoryNotFound,
    ProductHasDependencies,
    ProductNotFound,
    ProductTranslationAlreadyExists,
    ProductTranslationDeleteError,
    ProductTranslationNotFound,
    ProductValidationError,
)
from src.modules.products.models import Product
from src.modules.products.models_dto import (
    CatalogFiltersResponseDTO,
    CONSTRUCTION_NAMES,
    FilterApplicationDTO,
    FilterConstructionDTO,
    FilterMaterialDTO,
    FilterSizeRangeDTO,
    ProductBase,
    ProductCreate,
    ProductDetailResponseDTO,
    ProductListResponseDTO,
    ProductLocalizedResponseDTO,
    ProductResponseDTO,
    ProductTranslationCreate,
    ProductTranslationInsert,
    ProductTranslationResponseDTO,
    ProductTranslationUpdate,
    ProductUpdate,
    ProductUpdateIndexDTO,
)
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.service import PathBuilder
from src.modules.product_images.repository import ProductImageRepository
from src.modules.products.repository import (
    ProductRepository,
    ProductTranslationRepository,
)
from src.modules.rope_product_color.models_dto import ProductColorLocalizedResponseDTO
from src.modules.rope_products.models_dto import ProductVariantResponseDTO


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        translation_repo: ProductTranslationRepository,
        category_repo: CategoryRepository,
        session: AsyncSession,
        image_repo: Optional[ProductImageRepository] = None,
        image_manager: Optional[ImageManager] = None,
        path_builder: Optional[PathBuilder] = None,
    ):
        self.product_repo = product_repo
        self.translation_repo = translation_repo
        self.category_repo = category_repo
        self.session = session
        self.image_repo = image_repo
        self.image_manager = image_manager
        self.path_builder = path_builder

    async def create_product(self, data: ProductCreate) -> ProductResponseDTO:
        """Создание нового товара с переводами."""
        if not data.translations:
            raise ProductValidationError(
                "At least one translation is required when creating a Product."
            )

        locales = [t.locale for t in data.translations]
        if len(locales) != len(set(locales)):
            raise ProductValidationError(
                "Duplicate locales found in translations."
            )

        # Проверка существования категории
        category = await self.category_repo.get_by_id(data.category_id)
        if not category:
            raise ProductCategoryNotFound(
                f"Category with id {data.category_id} not found."
            )

        # Проверка уникальности slug
        existing = await self.product_repo.get_by_slug(data.slug)
        if existing:
            raise ProductAlreadyExists(
                f"Product with slug '{data.slug}' already exists."
            )

        if data.index is None:
            max_index = await self.product_repo.get_max_index()
            target_index = max_index + 1
        else:
            target_index = data.index
            await self.product_repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = ProductBase(
            category_id=data.category_id,
            slug=data.slug,
            product_type=data.product_type,
            price_unit=data.price_unit,
            has_configurator=data.has_configurator,
            construction_type=data.construction_type,
            index=target_index,
            is_active=data.is_active,
        )
        new_product = await self.product_repo.add_product(base_dto)
        await self.session.flush()

        for trans_data in data.translations:
            insert_dto = ProductTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                subtitle=trans_data.subtitle,
                description=trans_data.description,
                product_id=new_product.id,
            )
            await self.translation_repo.add_translation(insert_dto)

        await self.session.commit()
        created = await self.product_repo.get_by_id(new_product.id)
        return ProductResponseDTO.model_validate(created)

    async def get_all_products(
        self,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        product_type: Optional[str] = None,
        material_id: Optional[int] = None,
        construction_type: Optional[str] = None,
        application_codes: Optional[Union[List[str], str]] = None,
        diameter_min: Optional[float] = None,
        diameter_max: Optional[float] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        is_active: Optional[bool] = None,
        locale: Optional[Language] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        is_admin: bool = False,
    ) -> ProductListResponseDTO:
        """Получение списка товаров с фильтрацией, пагинацией и локализацией."""
        effective_active = is_active if is_admin else True
        parsed_app_codes: Optional[List[str]] = None
        if application_codes:
            if isinstance(application_codes, str):
                parsed_app_codes = [c.strip() for c in application_codes.split(",") if c.strip()]
            else:
                parsed_app_codes = []
                for item in application_codes:
                    for sub in item.split(","):
                        if sub.strip():
                            parsed_app_codes.append(sub.strip())

        products = await self.product_repo.get_all(
            category_id=category_id,
            category_slug=category_slug,
            product_type=product_type,
            material_id=material_id,
            construction_type=construction_type,
            application_codes=parsed_app_codes,
            diameter_min=diameter_min,
            diameter_max=diameter_max,
            price_min=price_min,
            price_max=price_max,
            is_active=effective_active,
            skip=skip,
            limit=limit,
        )
        total = await self.product_repo.count_all(
            category_id=category_id,
            category_slug=category_slug,
            product_type=product_type,
            material_id=material_id,
            construction_type=construction_type,
            application_codes=parsed_app_codes,
            diameter_min=diameter_min,
            diameter_max=diameter_max,
            price_min=price_min,
            price_max=price_max,
            is_active=effective_active,
        )

        product_ids = [p.id for p in products]
        aggregates = await self.product_repo.get_variants_aggregates(product_ids)

        return ProductListResponseDTO(
            items=[self._to_localized_dto(p, locale, aggregates) for p in products],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_product_by_id(
        self, product_id: int, locale: Optional[Language] = None, is_admin: bool = False
    ) -> Union[ProductLocalizedResponseDTO, ProductResponseDTO]:
        """Получение товара по ID со всеми переводами и связанными данными (или локализованного)."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")
        if not is_admin and not product.is_active:
            raise ProductNotFound(f"Product with id {product_id} not found.")
        if locale is not None:
            aggregates = await self.product_repo.get_variants_aggregates([product.id])
            return self._to_localized_dto(product, locale, aggregates)
        dto = ProductResponseDTO.model_validate(product)
        if not is_admin:
            dto.images = [img for img in dto.images if img.is_active]
            dto.variants = [v for v in dto.variants if v.is_active]
            dto.colors = [c for c in dto.colors if getattr(c, "is_active", True)]
            dto.applications = [a for a in dto.applications if a.is_active]
            dto.assigned_applications = [
                aa for aa in dto.assigned_applications
                if getattr(aa.application, "is_active", True)
            ]
        return dto

    async def get_product_by_slug(
        self, slug: str, locale: Optional[Language] = None, is_admin: bool = False
    ) -> Union[ProductLocalizedResponseDTO, ProductResponseDTO]:
        """Получение товара по slug со всеми переводами и связанными данными (или локализованного)."""
        product = await self.product_repo.get_by_slug(slug)
        if not product:
            raise ProductNotFound(f"Product with slug '{slug}' not found.")
        if not is_admin and not product.is_active:
            raise ProductNotFound(f"Product with slug '{slug}' not found.")
        if locale is not None:
            aggregates = await self.product_repo.get_variants_aggregates([product.id])
            return self._to_localized_dto(product, locale, aggregates)
        dto = ProductResponseDTO.model_validate(product)
        if not is_admin:
            dto.images = [img for img in dto.images if img.is_active]
            dto.variants = [v for v in dto.variants if v.is_active]
            dto.colors = [c for c in dto.colors if getattr(c, "is_active", True)]
            dto.applications = [a for a in dto.applications if a.is_active]
            dto.assigned_applications = [
                aa for aa in dto.assigned_applications
                if getattr(aa.application, "is_active", True)
            ]
        return dto

    async def get_catalog_filters(
        self,
        category_slug: Optional[str] = None,
        locale: Optional[Language] = None,
    ) -> CatalogFiltersResponseDTO:
        """Получение опций фильтрации каталога (материалы, конструкции, назначения, диапазон диаметров)."""
        target_locale = locale or Language.GER
        data = await self.product_repo.get_catalog_filter_data(category_slug=category_slug)

        # Materials
        materials_dto: List[FilterMaterialDTO] = []
        for m in data["materials"]:
            name = m._get_field_with_translation(
                lambda t: t.name, target_locale, fallback=Language.GER
            ) or m.code
            materials_dto.append(
                FilterMaterialDTO(id=m.id, code=m.code, name=name)
            )

        # Constructions
        constructions_dto: List[FilterConstructionDTO] = []
        codes = data["construction_codes"]
        if not codes and not category_slug:
            codes = ["hollow", "hm_core", "polyester_core", "none"]
        for c_code in codes:
            c_name = (
                CONSTRUCTION_NAMES.get(c_code, {}).get(target_locale)
                or CONSTRUCTION_NAMES.get(c_code, {}).get(Language.GER)
                or c_code.replace("_", " ").title()
            )
            constructions_dto.append(
                FilterConstructionDTO(code=c_code, name=c_name)
            )

        # Applications
        applications_dto: List[FilterApplicationDTO] = []
        for a in data["applications"]:
            name = a._get_field_with_translation(
                lambda t: t.name, target_locale, fallback=Language.GER
            ) or a.code
            applications_dto.append(
                FilterApplicationDTO(id=a.id, code=a.code, name=name)
            )

        # Size range
        size_range = FilterSizeRangeDTO(
            min=data["min_size"],
            max=data["max_size"],
        )

        return CatalogFiltersResponseDTO(
            materials=materials_dto,
            constructions=constructions_dto,
            applications=applications_dto,
            size_range=size_range,
        )

    async def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
    ) -> ProductResponseDTO:
        """Обновление атрибутов товара."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        if data.category_id is not None and data.category_id != product.category_id:
            category = await self.category_repo.get_by_id(data.category_id)
            if not category:
                raise ProductCategoryNotFound(
                    f"Category with id {data.category_id} not found."
                )

        if data.slug is not None and data.slug != product.slug:
            existing = await self.product_repo.get_by_slug(data.slug)
            if existing:
                raise ProductAlreadyExists(
                    f"Product with slug '{data.slug}' already exists."
                )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.product_repo.update_product(product_id, update_data)
        await self.session.commit()

        updated = await self.product_repo.get_by_id(product_id)
        return ProductResponseDTO.model_validate(updated)

    async def reorder_product(
        self,
        product_id: int,
        data: ProductUpdateIndexDTO,
    ) -> ProductResponseDTO:
        """Изменение порядкового индекса товара с автоматическим сдвигом соседей."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        if product.index != data.new_index:
            await self.product_repo.reorder_index(
                obj_id=product_id,
                old_index=product.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated = await self.product_repo.get_by_id(product_id)
        return ProductResponseDTO.model_validate(updated)

    async def delete_product(self, product_id: int) -> None:
        """Удаление товара со всеми зависимыми сущностями и медиафайлами."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        has_deps = await self.product_repo.has_dependencies(product_id)
        if has_deps:
            raise ProductHasDependencies(
                f"Cannot delete Product with id {product_id} because it is referenced by other entities."
            )

        # 1. Физическое удаление файлов изображений с диска
        images = []
        if self.image_repo:
            images = await self.image_repo.get_by_product_id(product_id)
        elif getattr(product, "images", None):
            images = product.images

        if self.image_manager and images:
            for img in images:
                if getattr(img, "image_url", None):
                    self.image_manager.delete_image(img.image_url)

        # Удаление всей директории товара на диске (включая папку original/ при наличии)
        if self.path_builder:
            product_dir = self.path_builder.get_product_dir(product_id)
            if product_dir.exists() and product_dir.is_dir():
                shutil.rmtree(product_dir, ignore_errors=True)

        # 2. Удаление записей изображений через image_repo (если внедрен)
        if self.image_repo:
            await self.image_repo.delete_by_product_id(product_id)

        # 3. Удаление самого товара и его зависимых данных через product_repo
        await self.product_repo.delete_product(product_id)
        await self.product_repo.shift_indexes_after_delete(product.index)
        await self.session.commit()

    async def create_translation(
        self,
        product_id: int,
        data: ProductTranslationCreate,
    ) -> ProductTranslationResponseDTO:
        """Добавление перевода для товара."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        existing = await self.translation_repo.get_by_product_and_locale(
            product_id=product_id,
            locale=data.locale,
        )
        if existing:
            raise ProductTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for product {product_id}."
            )

        insert_dto = ProductTranslationInsert(
            locale=data.locale,
            name=data.name,
            subtitle=data.subtitle,
            description=data.description,
            product_id=product_id,
        )
        trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        return ProductTranslationResponseDTO.model_validate(trans)

    async def update_translation(
        self,
        translation_id: int,
        data: ProductTranslationUpdate,
    ) -> ProductTranslationResponseDTO:
        """Обновление перевода товара."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise ProductTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()

        updated = await self.translation_repo.get_by_id(translation_id)
        return ProductTranslationResponseDTO.model_validate(updated)

    async def delete_translation(
        self,
        translation_id: int,
    ) -> None:
        """Удаление перевода товара (с запретом удаления последнего)."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise ProductTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        count = await self.translation_repo.count_by_product_id(trans.product_id)
        if count <= 1:
            raise ProductTranslationDeleteError(
                "Cannot delete the only remaining translation of the product."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()

    def _to_localized_dto(
        self,
        product: Product,
        locale: Optional[Language],
        aggregates: Optional[dict] = None,
    ) -> ProductLocalizedResponseDTO:
        """Конвертация в локализованное DTO с fallback-логикой и всеми подгруженными связями."""
        target_locale = locale or Language.ENG
        name = product._get_field_with_translation(
            lambda t: t.name,
            target_locale,
            fallback=Language.GER,
        )
        subtitle = product._get_field_with_translation(
            lambda t: t.subtitle,
            target_locale,
            fallback=Language.GER,
        )
        description = product._get_field_with_translation(
            lambda t: t.description,
            target_locale,
            fallback=Language.GER,
        )

        specs_dto: List[ProductSpecificationLocalizedResponseDTO] = []
        for spec in getattr(product, "specifications", []):
            spec_name = spec._get_field_with_translation(
                lambda t: t.name,
                target_locale,
                fallback=Language.GER,
            )
            spec_value = spec._get_field_with_translation(
                lambda t: t.value,
                target_locale,
                fallback=Language.GER,
            )
            specs_dto.append(
                ProductSpecificationLocalizedResponseDTO(
                    id=spec.id,
                    product_id=spec.product_id,
                    index=spec.index,
                    name=spec_name if spec_name is not None else "",
                    value=spec_value if spec_value is not None else "",
                )
            )

        apps_dto: List[ProductApplicationLocalizedResponseDTO] = []
        for assigned in getattr(product, "assigned_applications", []):
            app = getattr(assigned, "application", None)
            if app and getattr(app, "is_active", True):
                app_name = app._get_field_with_translation(
                    lambda t: t.name,
                    target_locale,
                    fallback=Language.GER,
                )
                apps_dto.append(
                    ProductApplicationLocalizedResponseDTO(
                        id=app.id,
                        code=app.code,
                        index=app.index,
                        is_active=app.is_active,
                        name=app_name if app_name is not None else app.code,
                    )
                )

        images_dto = [
            ProductImageResponseDTO.model_validate(img)
            for img in getattr(product, "images", [])
            if getattr(img, "is_active", True)
        ]

        variants_dto = [
            ProductVariantResponseDTO.model_validate(v)
            for v in getattr(product, "variants", [])
            if getattr(v, "is_active", True)
        ]

        colors_dto: List[ProductColorLocalizedResponseDTO] = []
        for pc in getattr(product, "colors", []):
            c = getattr(pc, "color", None)
            if c and getattr(c, "is_active", True):
                c_name = c._get_field_with_translation(
                    lambda t: t.name,
                    target_locale,
                    fallback=Language.GER,
                )
                color_loc = ColorLocalizedResponseDTO(
                    id=c.id,
                    code=c.code,
                    hex=c.hex,
                    index=c.index,
                    is_active=c.is_active,
                    name=c_name if c_name is not None else c.code,
                )
                colors_dto.append(
                    ProductColorLocalizedResponseDTO(
                        id=pc.id,
                        product_id=pc.product_id,
                        color_id=pc.color_id,
                        index=pc.index,
                        color=color_loc,
                    )
                )

        agg = (aggregates or {}).get(product.id) if aggregates else None
        if agg:
            price_from = agg.get("price_from")
            size_min = agg.get("size_min")
            size_max = agg.get("size_max")
            variants_count = agg.get("variants_count", 0)
        else:
            price_from = product.price_from
            size_min = product.size_min
            size_max = product.size_max
            variants_count = product.variants_count

        return ProductLocalizedResponseDTO(
            id=product.id,
            category_id=product.category_id,
            slug=product.slug,
            product_type=product.product_type,
            price_unit=product.price_unit,
            has_configurator=product.has_configurator,
            construction_type=product.construction_type,
            index=product.index,
            is_active=product.is_active,
            name=name if name else "No Translation",
            subtitle=subtitle,
            description=description,
            main_image_url=product.main_image_url,
            price_from=price_from,
            size_min=size_min,
            size_max=size_max,
            variants_count=variants_count,
            images=images_dto,
            specifications=specs_dto,
            applications=apps_dto,
            variants=variants_dto,
            colors=colors_dto,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
