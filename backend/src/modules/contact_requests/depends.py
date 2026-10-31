from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.database.database import get_db
from src.modules.contact_requests.repository import ContactRequestRepository
from src.modules.contact_requests.service import ContactRequestService
from src.modules.depends import get_config
from src.modules.notifications.depends import get_notification_service
from src.modules.notifications.service import NotificationService


async def get_contact_request_repository(
    session: AsyncSession = Depends(get_db),
) -> ContactRequestRepository:
    return ContactRequestRepository(session=session)


async def get_contact_request_service(
    session: AsyncSession = Depends(get_db),
    repo: ContactRequestRepository = Depends(get_contact_request_repository),
    notification_service: NotificationService = Depends(get_notification_service),
    config: Config = Depends(get_config),
) -> ContactRequestService:
    return ContactRequestService(
        repo=repo,
        session=session,
        notification_service=notification_service,
        config=config,
    )
