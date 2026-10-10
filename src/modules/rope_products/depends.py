from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.rope_products.repository import RopeProductRepository, RopeVariantRepository
from src.modules.rope_products.service import RopeProductsService


def get_rope_product_repository(
    session: AsyncSession = Depends(get_db)
) -> RopeProductRepository:
    return RopeProductRepository(session=session)


def get_rope_variant_repository(
    session: AsyncSession = Depends(get_db)
) -> RopeVariantRepository:
    return RopeVariantRepository(session=session)


def get_rope_products_service(
    session: AsyncSession = Depends(get_db),
    product_repo: RopeProductRepository = Depends(get_rope_product_repository),
    variant_repo: RopeVariantRepository = Depends(get_rope_variant_repository),
) -> RopeProductsService:
    return RopeProductsService(
        product_repo=product_repo,
        variant_repo=variant_repo,
        session=session,
    )
