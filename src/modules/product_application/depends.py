from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.product_application.repository import (
    ProductApplicationRepository,
    ProductApplicationTranslationRepository,
    ProductAssignedApplicationRepository,
)
from src.modules.product_application.service import ProductApplicationService
from src.modules.products.repository import ProductRepository


def get_product_application_service(
    session: AsyncSession = Depends(get_db),
) -> ProductApplicationService:
    return ProductApplicationService(
        app_repo=ProductApplicationRepository(session=session),
        trans_repo=ProductApplicationTranslationRepository(session=session),
        assigned_repo=ProductAssignedApplicationRepository(session=session),
        product_repo=ProductRepository(session=session),
        session_db=session,
    )
