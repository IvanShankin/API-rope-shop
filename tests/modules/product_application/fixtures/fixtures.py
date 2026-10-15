import pytest_asyncio
from tests.modules.product_application.fixtures.models_dto import (
    CreateProductApplicationFixtureDTO,
    CreateProductApplicationTranslationFixtureDTO,
    CreateProductAssignedApplicationFixtureDTO,
)
from src.modules.product_application.models_dto import (
    ProductApplicationResponseDTO,
    ProductApplicationTranslationResponseDTO,
    ProductAssignedApplicationResponseDTO,
)
from tests.modules.product_application.fixtures.factory import (
    create_product_application_factory,
    create_product_application_translation_factory,
    create_product_assigned_application_factory,
)


@pytest_asyncio.fixture(scope="function")
async def create_product_application_fixture(
    not_open_session_db
):
    async def _factory(
        new_app: CreateProductApplicationFixtureDTO = CreateProductApplicationFixtureDTO(),
    ) -> ProductApplicationResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_application_factory(
                session_db=session,
                new_app=new_app,
            )
    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_product_application_translation_fixture(
    not_open_session_db
):
    async def _factory(
        new_trans: CreateProductApplicationTranslationFixtureDTO = CreateProductApplicationTranslationFixtureDTO(),
    ) -> ProductApplicationTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_application_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )
    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_product_assigned_application_fixture(
    not_open_session_db
):
    async def _factory(
        new_assign: CreateProductAssignedApplicationFixtureDTO = CreateProductAssignedApplicationFixtureDTO(),
    ) -> ProductAssignedApplicationResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_assigned_application_factory(
                session_db=session,
                new_assign=new_assign,
            )
    return _factory
