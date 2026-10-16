from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.handlers_files.depends import get_image_manager
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.depends import get_path_builder
from src.modules.path_builder.service import PathBuilder
from src.modules.product_images.repository import ProductImageRepository
from src.modules.product_images.service import ProductImageService
from src.modules.products.depends import get_product_repository
from src.modules.products.repository import ProductRepository


async def get_product_image_repository(
    session: AsyncSession = Depends(get_db),
) -> ProductImageRepository:
    return ProductImageRepository(session=session)


async def get_product_image_service(
    session: AsyncSession = Depends(get_db),
    repo: ProductImageRepository = Depends(get_product_image_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    image_manager: ImageManager = Depends(get_image_manager),
    path_builder: PathBuilder = Depends(get_path_builder),
) -> ProductImageService:
    return ProductImageService(
        repo=repo,
        product_repo=product_repo,
        session=session,
        image_manager=image_manager,
        path_builder=path_builder,
    )
