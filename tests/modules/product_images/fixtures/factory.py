from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.product_images.models import ProductImage
from src.modules.product_images.models_dto import ProductImageResponseDTO
from tests.helpers.functions import random_string
from tests.modules.product_images.fixtures.models_dto import (
    CreateProductImageFixtureDTO,
)
from tests.modules.products.fixtures.factory import create_product_factory


async def create_product_image_factory(
    session_db: AsyncSession,
    new_image: CreateProductImageFixtureDTO = CreateProductImageFixtureDTO(),
) -> ProductImageResponseDTO:
    if new_image.product_id is None:
        prod = await create_product_factory(session_db=session_db)
        product_id = prod.id
    else:
        product_id = new_image.product_id

    image_url = (
        new_image.image_url
        if new_image.image_url is not None
        else f"/media/products/{product_id}/{random_string()}.webp"
    )
    is_main = new_image.is_main if new_image.is_main is not None else False
    index = new_image.index if new_image.index is not None else 0
    is_active = new_image.is_active if new_image.is_active is not None else True

    image = ProductImage(
        product_id=product_id,
        image_url=image_url,
        is_main=is_main,
        index=index,
        is_active=is_active,
    )
    session_db.add(image)
    await session_db.commit()
    await session_db.refresh(image)

    return ProductImageResponseDTO.model_validate(image)
