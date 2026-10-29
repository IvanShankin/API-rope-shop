from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.rope_allowed_splice.repository import RopeAllowedSpliceRepository
from src.modules.rope_allowed_splice.service import RopeAllowedSpliceService


def get_rope_allowed_splice_repository(
    session: AsyncSession = Depends(get_db)
) -> RopeAllowedSpliceRepository:
    return RopeAllowedSpliceRepository(session=session)


def get_rope_allowed_splice_service(
    session: AsyncSession = Depends(get_db),
    repo: RopeAllowedSpliceRepository = Depends(get_rope_allowed_splice_repository),
) -> RopeAllowedSpliceService:
    return RopeAllowedSpliceService(repo=repo, session=session)
