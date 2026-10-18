import pytest_asyncio

from src.modules.product_images.models_dto import ProductImageResponseDTO
from tests.modules.product_images.fixtures.factory import (
    create_product_image_factory,
)
from tests.modules.product_images.fixtures.models_dto import (
    CreateProductImageFixtureDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_product_image_fixture(not_open_session_db):
    async def _factory(
        new_image: CreateProductImageFixtureDTO = CreateProductImageFixtureDTO(),
    ) -> ProductImageResponseDTO:
        async with not_open_session_db() as session:
            return await create_product_image_factory(
                session_db=session,
                new_image=new_image,
            )

    return _factory
