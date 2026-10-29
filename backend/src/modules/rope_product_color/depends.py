from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.rope_product_color.repository import ProductColorRepository
from src.modules.rope_product_color.service import RopeProductColorService


def get_rope_product_color_service(
    session: AsyncSession = Depends(get_db),
) -> RopeProductColorService:
    return RopeProductColorService(
        repo=ProductColorRepository(session=session),
        session=session,
    )
