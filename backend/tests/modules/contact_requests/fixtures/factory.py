from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contact_requests.models import ContactRequest
from src.modules.contact_requests.models_dto import ContactRequestResponseDTO
from tests.helpers.functions import random_string
from tests.modules.contact_requests.fixtures.models_dto import (
    CreateContactRequestFixtureDTO,
)


async def create_contact_request_factory(
    session_db: AsyncSession,
    new_contact: CreateContactRequestFixtureDTO = CreateContactRequestFixtureDTO(),
) -> ContactRequestResponseDTO:
    name = (
        new_contact.name
        if new_contact.name is not None
        else f"Company {random_string(6)}"
    )
    email = (
        new_contact.email
        if new_contact.email is not None
        else f"contact_{random_string(6)}@example.com"
    )
    phone = (
        new_contact.phone
        if new_contact.phone is not None
        else "+1 (555) 123-4567"
    )
    message = (
        new_contact.message
        if new_contact.message is not None
        else f"Message body text {random_string(10)}"
    )

    contact = ContactRequest(
        name=name,
        email=email,
        phone=phone,
        message=message,
    )
    session_db.add(contact)
    await session_db.commit()
    await session_db.refresh(contact)

    return ContactRequestResponseDTO.model_validate(contact)
