from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from tests.modules.rope_products.fixtures.factory import (
    create_rope_product_factory,
    create_rope_variant_factory,
)
from src.modules.rope_products.models import RopeConfiguratorSetting, ProductVariant


@pytest_asyncio.fixture(scope="function")
async def create_rope_product_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateRopeProductFixtureDTO], Awaitable[RopeConfiguratorSetting]]:
    async def _factory(
        new_product: CreateRopeProductFixtureDTO = CreateRopeProductFixtureDTO(),
    ) -> RopeConfiguratorSetting:
        return await create_rope_product_factory(
            session_db=session_db,
            new_product=new_product,
        )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_rope_variant_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateRopeVariantFixtureDTO], Awaitable[ProductVariant]]:
    async def _factory(
        new_variant: CreateRopeVariantFixtureDTO = CreateRopeVariantFixtureDTO(),
    ) -> ProductVariant:
        return await create_rope_variant_factory(
            session_db=session_db,
            new_variant=new_variant,
        )

    return _factory
