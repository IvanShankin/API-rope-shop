from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.products.repository import ProductRepository
from src.modules.product_specification.repository import (
    ProductSpecificationRepository,
    ProductSpecificationTranslationRepository,
)
from src.modules.product_specification.service import ProductSpecificationService


def get_product_specification_service(
    session: AsyncSession = Depends(get_db),
) -> ProductSpecificationService:
    return ProductSpecificationService(
        spec_repo=ProductSpecificationRepository(session=session),
        trans_repo=ProductSpecificationTranslationRepository(session=session),
        product_repo=ProductRepository(session=session),
        session_db=session,
    )
