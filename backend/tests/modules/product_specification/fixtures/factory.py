from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.functions import random_string
from tests.modules.products.fixtures.factory import create_product_factory
from tests.modules.product_specification.fixtures.models_dto import (
    CreateProductSpecificationFixtureDTO,
    CreateProductSpecificationTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.product_specification.models import (
    ProductSpecification,
    ProductSpecificationTranslation,
)
from src.modules.product_specification.models_dto import (
    ProductSpecificationResponseDTO,
    ProductSpecificationTranslationResponseDTO,
)


async def create_product_specification_factory(
    session_db: AsyncSession,
    new_spec: CreateProductSpecificationFixtureDTO = CreateProductSpecificationFixtureDTO(),
) -> ProductSpecificationResponseDTO:
    if new_spec.product_id is None:
        prod = await create_product_factory(session_db=session_db)
        product_id = prod.id
    else:
        product_id = new_spec.product_id

    spec = ProductSpecification(
        product_id=product_id,
        index=0 if new_spec.index is None else new_spec.index,
    )
    session_db.add(spec)
    await session_db.flush()

    # Default translation
    trans = ProductSpecificationTranslation(
        specification_id=spec.id,
        locale=new_spec.locale if new_spec.locale is not None else Language.ENG,
        name=new_spec.name if new_spec.name is not None else random_string(),
        value=new_spec.value if new_spec.value is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(ProductSpecification)
        .where(ProductSpecification.id == spec.id)
        .options(selectinload(ProductSpecification.translations))
    )
    spec = result.scalar_one()

    return ProductSpecificationResponseDTO.model_validate(spec)


async def create_product_specification_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateProductSpecificationTranslationFixtureDTO = CreateProductSpecificationTranslationFixtureDTO(),
) -> ProductSpecificationTranslationResponseDTO:
    if new_trans.specification_id is None:
        spec = await create_product_specification_factory(session_db=session_db)
        specification_id = spec.id
    else:
        specification_id = new_trans.specification_id

    trans = ProductSpecificationTranslation(
        specification_id=specification_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
        value=new_trans.value if new_trans.value is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return ProductSpecificationTranslationResponseDTO.model_validate(trans)
