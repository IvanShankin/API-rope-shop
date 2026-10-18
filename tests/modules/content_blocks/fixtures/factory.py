from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.content_blocks.models import (
    ContentBlock,
    ContentBlockTranslation,
)
from src.modules.content_blocks.models_dto import (
    ContentBlockResponseDTO,
    ContentBlockTranslationResponseDTO,
)
from tests.helpers.functions import random_string
from tests.modules.content_blocks.fixtures.models_dto import (
    CreateContentBlockFixtureDTO,
    CreateContentBlockTranslationFixtureDTO,
)


async def create_content_block_factory(
    session_db: AsyncSession,
    new_block: CreateContentBlockFixtureDTO = CreateContentBlockFixtureDTO(),
) -> ContentBlockResponseDTO:
    page_code = (
        new_block.page_code
        if new_block.page_code is not None
        else f"page_{random_string(6)}"
    )
    block_code = (
        new_block.block_code
        if new_block.block_code is not None
        else f"block_{random_string(8)}"
    )
    is_active = (
        new_block.is_active if new_block.is_active is not None else True
    )
    locale = new_block.locale if new_block.locale is not None else Language.ENG
    title = (
        new_block.title
        if new_block.title is not None
        else f"Title {random_string(6)}"
    )
    content = (
        new_block.content
        if new_block.content is not None
        else f"Content body text {random_string(12)}"
    )

    block = ContentBlock(
        page_code=page_code,
        block_code=block_code,
        is_active=is_active,
    )
    session_db.add(block)
    await session_db.flush()

    translation = ContentBlockTranslation(
        content_block_id=block.id,
        locale=locale,
        title=title,
        content=content,
    )
    session_db.add(translation)
    await session_db.commit()

    stmt = (
        select(ContentBlock)
        .where(ContentBlock.id == block.id)
        .options(selectinload(ContentBlock.translations))
    )
    res = await session_db.execute(stmt)
    loaded = res.scalar_one()

    return ContentBlockResponseDTO.model_validate(loaded)


async def create_content_block_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateContentBlockTranslationFixtureDTO = CreateContentBlockTranslationFixtureDTO(),
) -> ContentBlockTranslationResponseDTO:
    if new_trans.content_block_id is None:
        block_dto = await create_content_block_factory(session_db=session_db)
        block_id = block_dto.id
    else:
        block_id = new_trans.content_block_id

    locale = new_trans.locale if new_trans.locale is not None else Language.GER
    title = (
        new_trans.title
        if new_trans.title is not None
        else f"Translated Title {random_string(6)}"
    )
    content = (
        new_trans.content
        if new_trans.content is not None
        else f"Translated Content {random_string(10)}"
    )

    translation = ContentBlockTranslation(
        content_block_id=block_id,
        locale=locale,
        title=title,
        content=content,
    )
    session_db.add(translation)
    await session_db.commit()
    await session_db.refresh(translation)

    return ContentBlockTranslationResponseDTO.model_validate(translation)
