from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.splice_materials.repository import SpliceMaterialRepository
from src.modules.splice_materials.service import SpliceMaterialService


def get_splice_material_service(
    session: AsyncSession = Depends(get_db),
) -> SpliceMaterialService:
    return SpliceMaterialService(
        material_repo=SpliceMaterialRepository(session=session),
        session=session
    )
