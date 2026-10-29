from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.contact_requests.repository import ContactRequestRepository
from src.modules.contact_requests.service import ContactRequestService


async def get_contact_request_repository(
    session: AsyncSession = Depends(get_db),
) -> ContactRequestRepository:
    return ContactRequestRepository(session=session)


async def get_contact_request_service(
    session: AsyncSession = Depends(get_db),
    repo: ContactRequestRepository = Depends(get_contact_request_repository),
) -> ContactRequestService:
    return ContactRequestService(
        repo=repo,
        session=session,
    )
