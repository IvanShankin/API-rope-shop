from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.functions import random_string
from tests.modules.categories.fixtures.factory import create_category_factory
from tests.modules.products.fixtures.models_dto import (
    CreateProductFixtureDTO,
    CreateProductTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.products.models import Product, ProductTranslation, ProductType
from src.modules.products.models_dto import (
    ProductResponseDTO,
    ProductTranslationResponseDTO,
)


async def create_product_factory(
    session_db: AsyncSession,
    new_product: CreateProductFixtureDTO = CreateProductFixtureDTO()
) -> ProductResponseDTO:
    if new_product.category_id is None:
        cat = await create_category_factory(session_db=session_db)
        category_id = cat.id
    else:
        category_id = new_product.category_id

    product = Product(
        category_id=category_id,
        slug=random_string() if new_product.slug is None else new_product.slug,
        product_type=new_product.product_type or ProductType.ROPE.value,
        index=1 if new_product.index is None else new_product.index,
        is_active=True if new_product.is_active is None else new_product.is_active,
    )
    session_db.add(product)
    await session_db.flush()

    # Default translation
    trans = ProductTranslation(
        product_id=product.id,
        locale=new_product.locale if new_product.locale is not None else Language.ENG,
        name=new_product.name if new_product.name is not None else random_string(),
        description=new_product.description,
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(Product)
        .where(Product.id == product.id)
        .options(
            selectinload(Product.translations),
            selectinload(Product.images),
            selectinload(Product.category),
        )
    )
    product = result.scalar_one()

    return ProductResponseDTO.model_validate(product)


async def create_product_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateProductTranslationFixtureDTO = CreateProductTranslationFixtureDTO()
) -> ProductTranslationResponseDTO:
    if new_trans.product_id is None:
        prod = await create_product_factory(session_db=session_db)
        product_id = prod.id
    else:
        product_id = new_trans.product_id

    trans = ProductTranslation(
        product_id=product_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
        description=new_trans.description,
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return ProductTranslationResponseDTO.model_validate(trans)
