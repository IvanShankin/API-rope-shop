import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.modules.base.exception import NoDataForUpdate
from src.modules.contact_requests.exception import ContactRequestNotFound
from src.modules.contact_requests.models import ContactRequest
from src.modules.contact_requests.models_dto import (
    ContactRequestCreateDTO,
    ContactRequestResponseDTO,
    ContactRequestUpdateDTO,
)
from src.modules.contact_requests.repository import ContactRequestRepository
from src.modules.notifications.service import NotificationService

logger = logging.getLogger(__name__)


DEFAULT_CONTACT_REQUEST = {
    "name": "General Contact",
    "email": "info@ropeshop.com",
    "phone": "+1 (555) 019-2834",
    "message": "Welcome to our rope shop. Feel free to contact us with any inquiries.",
}


class ContactRequestService:
    def __init__(
        self,
        repo: ContactRequestRepository,
        session: AsyncSession,
        notification_service: NotificationService,
        config: Config,
    ):
        self.repo = repo
        self.session = session
        self.notification_service = notification_service
        self.config = config

    async def create_contact(
        self,
        data: ContactRequestCreateDTO,
    ) -> ContactRequestResponseDTO:
        """
        Создание новой входящей заявки/сообщения от клиента (Contact Us).
        """
        contact = ContactRequest(**data.model_dump())
        self.repo.add_contact(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        response_dto = ContactRequestResponseDTO.model_validate(contact)

        # Асинхронная отправка уведомлений в ТГ и на почту без блокировки ответа клиенту
        try:
            settings = await self.notification_service.get_settings()
            asyncio.create_task(
                self.notification_service.notify_new_contact_request(
                    contact=response_dto,
                    settings=settings,
                )
            )
        except Exception as e:
            logger.error("Failed to schedule contact request notifications: %s", e, exc_info=True)

        return response_dto

    async def get_contact_requests(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContactRequestResponseDTO]:
        """
        Получение списка входящих заявок (только для администратора).
        """
        requests = await self.repo.get_all(limit=limit, offset=offset)
        return [ContactRequestResponseDTO.model_validate(r) for r in requests]

    async def get_contact(self) -> ContactRequestResponseDTO:
        """
        Получение контактных данных (доступно всем).
        """
        contact = await self.repo.get_first()
        if not contact:
            raise ContactRequestNotFound("No contact requests found.")

        return ContactRequestResponseDTO.model_validate(contact)

    async def get_contact_by_id(self, contact_id: int) -> ContactRequestResponseDTO:
        """
        Получение контактных данных по конкретному ID (доступно всем).
        """
        contact = await self.repo.get_by_id(contact_id)
        if not contact:
            raise ContactRequestNotFound(
                f"ContactRequest with id {contact_id} not found."
            )

        return ContactRequestResponseDTO.model_validate(contact)

    async def update_contact(
        self,
        data: ContactRequestUpdateDTO,
    ) -> ContactRequestResponseDTO:
        """
        Обновление контактных данных (только админ).
        """
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("No data provided for update.")

        contact = await self.repo.get_first()
        if not contact:
            raise ContactRequestNotFound("No contact requests found.")

        await self.repo.update_contact(contact.id, update_dict)
        await self.session.commit()
        await self.session.refresh(contact)

        return ContactRequestResponseDTO.model_validate(contact)

    async def update_contact_by_id(
        self,
        contact_id: int,
        data: ContactRequestUpdateDTO,
    ) -> ContactRequestResponseDTO:
        """
        Обновление контактных данных по конкретному ID (только админ).
        """
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("No data provided for update.")

        contact = await self.repo.get_by_id(contact_id)
        if not contact:
            raise ContactRequestNotFound(
                f"ContactRequest with id {contact_id} not found."
            )

        await self.repo.update_contact(contact_id, update_dict)
        await self.session.commit()
        await self.session.refresh(contact)

        return ContactRequestResponseDTO.model_validate(contact)

    async def _initialize_default_contact(self) -> ContactRequest:
        """Создание начальной строки контактных данных по умолчанию."""
        contact = ContactRequest(**DEFAULT_CONTACT_REQUEST)
        self.repo.add_contact(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact
