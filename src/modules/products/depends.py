from typing import TYPE_CHECKING

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.categories.repository import CategoryRepository
from src.modules.handlers_files.depends import get_image_manager
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.depends import get_path_builder
from src.modules.path_builder.service import PathBuilder
from src.modules.product_images.repository import ProductImageRepository
from src.modules.products.repository import (
    ProductRepository,
    ProductTranslationRepository,
)

if TYPE_CHECKING:
    from src.modules.products.service import ProductService


async def get_product_repository(
    session: AsyncSession = Depends(get_db),
) -> ProductRepository:
    return ProductRepository(session=session)


async def get_product_translation_repository(
    session: AsyncSession = Depends(get_db),
) -> ProductTranslationRepository:
    return ProductTranslationRepository(session=session)


async def get_category_repository(
    session: AsyncSession = Depends(get_db),
) -> CategoryRepository:
    return CategoryRepository(session=session)


async def get_product_image_repository(
    session: AsyncSession = Depends(get_db),
) -> ProductImageRepository:
    return ProductImageRepository(session=session)


async def get_product_service(
    product_repo: ProductRepository = Depends(get_product_repository),
    translation_repo: ProductTranslationRepository = Depends(get_product_translation_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
    image_repo: ProductImageRepository = Depends(get_product_image_repository),
    image_manager: ImageManager = Depends(get_image_manager),
    path_builder: PathBuilder = Depends(get_path_builder),
    session: AsyncSession = Depends(get_db),
) -> "ProductService":
    from src.modules.products.service import ProductService

    return ProductService(
        product_repo=product_repo,
        translation_repo=translation_repo,
        category_repo=category_repo,
        session=session,
        image_repo=image_repo,
        image_manager=image_manager,
        path_builder=path_builder,
    )
