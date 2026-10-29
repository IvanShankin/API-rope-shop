from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NoDataForUpdate
from src.modules.contact_requests.exception import ContactRequestNotFound
from src.modules.contact_requests.models import ContactRequest
from src.modules.contact_requests.models_dto import (
    ContactRequestCreateDTO,
    ContactRequestResponseDTO,
    ContactRequestUpdateDTO,
)
from src.modules.contact_requests.repository import ContactRequestRepository


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
    ):
        self.repo = repo
        self.session = session

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
        return ContactRequestResponseDTO.model_validate(contact)

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
        Если запись в таблице еще не создана, инициализирует дефолтную запись.
        """
        contact = await self.repo.get_first()
        if not contact:
            contact = await self._initialize_default_contact()

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
            contact = await self._initialize_default_contact()

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
