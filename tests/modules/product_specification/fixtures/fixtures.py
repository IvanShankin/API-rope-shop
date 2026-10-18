import pytest_asyncio
from tests.modules.product_specification.fixtures.models_dto import (
    CreateProductSpecificationFixtureDTO,
    CreateProductSpecificationTranslationFixtureDTO,
)
from src.modules.product_specification.models_dto import (
    ProductSpecificationResponseDTO,
    ProductSpecificationTranslationResponseDTO,
)
from tests.modules.product_specification.fixtures.factory import (
    create_product_specification_factory,
    create_product_specification_translation_factory,
)


@pytest_asyncio.fixture(scope="function")
async def create_product_specification_fixture(
    not_open_session_db
):
    async def _factory(
        new_spec: CreateProductSpecificationFixtureDTO = CreateProductSpecificationFixtureDTO(),
    ) -> ProductSpecificationResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_specification_factory(
                session_db=session,
                new_spec=new_spec,
            )
    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_product_specification_translation_fixture(
    not_open_session_db
):
    async def _factory(
        new_trans: CreateProductSpecificationTranslationFixtureDTO = CreateProductSpecificationTranslationFixtureDTO(),
    ) -> ProductSpecificationTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_specification_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )
    return _factory
