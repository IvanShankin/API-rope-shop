import pytest_asyncio
from tests.modules.products.fixtures.models_dto import (
    CreateProductFixtureDTO,
    CreateProductTranslationFixtureDTO,
)
from src.modules.products.models_dto import (
    ProductResponseDTO,
    ProductTranslationResponseDTO,
)
from tests.modules.products.fixtures.factory import (
    create_product_factory,
    create_product_translation_factory,
)


@pytest_asyncio.fixture(scope="function")
async def create_product_fixture(
    not_open_session_db
):
    async def _factory(
        new_product: CreateProductFixtureDTO = CreateProductFixtureDTO(),
    ) -> ProductResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_factory(
                session_db=session,
                new_product=new_product,
            )
    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_product_translation_fixture(
    not_open_session_db
):
    async def _factory(
        new_trans: CreateProductTranslationFixtureDTO = CreateProductTranslationFixtureDTO(),
    ) -> ProductTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )
    return _factory
