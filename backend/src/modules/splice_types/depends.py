from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.handlers_files.depends import get_image_manager
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.depends import get_path_builder
from src.modules.path_builder.service import PathBuilder
from src.modules.splice_types.repository import SpliceTypeRepository, SpliceTypeTranslationRepository
from src.modules.splice_types.service import SpliceTypeService


def get_splice_type_service(
    session: AsyncSession = Depends(get_db),
    image_manager: ImageManager = Depends(get_image_manager),
    path_builder: PathBuilder = Depends(get_path_builder),
) -> SpliceTypeService:
    return SpliceTypeService(
        type_repo=SpliceTypeRepository(session=session),
        translation_repo=SpliceTypeTranslationRepository(session=session),
        session=session,
        image_manager=image_manager,
        path_builder=path_builder,
    )
