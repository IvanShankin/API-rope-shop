import pytest_asyncio

from src.modules.contact_requests.models_dto import ContactRequestResponseDTO
from tests.modules.contact_requests.fixtures.factory import (
    create_contact_request_factory,
)
from tests.modules.contact_requests.fixtures.models_dto import (
    CreateContactRequestFixtureDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_contact_request_fixture(not_open_session_db):
    async def _factory(
        new_contact: CreateContactRequestFixtureDTO = CreateContactRequestFixtureDTO(),
    ) -> ContactRequestResponseDTO:
        async with not_open_session_db() as session:
            return await create_contact_request_factory(
                session_db=session,
                new_contact=new_contact,
            )

    return _factory
