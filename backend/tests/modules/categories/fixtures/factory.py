from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.functions import random_string
from tests.modules.categories.fixtures.models_dto import (
    CreateCategoryFixtureDTO,
    CreateCategoryTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.categories.models import Category, CategoryTranslation
from src.modules.categories.models_dto import (
    CategoryResponseDTO,
    CategoryTranslationResponseDTO,
)


async def create_category_factory(
    session_db: AsyncSession,
    new_category: CreateCategoryFixtureDTO = CreateCategoryFixtureDTO()
) -> CategoryResponseDTO:
    category = Category(
        slug=random_string() if new_category.slug is None else new_category.slug,
        image_url=new_category.image_url,
        index=1 if new_category.index is None else new_category.index,
        is_active=True if new_category.is_active is None else new_category.is_active,
    )
    session_db.add(category)
    await session_db.flush()

    # Default translation
    trans = CategoryTranslation(
        category_id=category.id,
        locale=new_category.locale if new_category.locale is not None else Language.ENG,
        name=new_category.name if new_category.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(Category).where(Category.id == category.id).options(selectinload(Category.translations))
    )
    category = result.scalar_one()

    return CategoryResponseDTO.model_validate(category)


async def create_category_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateCategoryTranslationFixtureDTO = CreateCategoryTranslationFixtureDTO()
) -> CategoryTranslationResponseDTO:
    if new_trans.category_id is None:
        cat = await create_category_factory(session_db=session_db)
        category_id = cat.id
    else:
        category_id = new_trans.category_id

    trans = CategoryTranslation(
        category_id=category_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return CategoryTranslationResponseDTO.model_validate(trans)
