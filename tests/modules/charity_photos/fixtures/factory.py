from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.modules.base.database_model import Language
from src.modules.charity_photos.models import CharityPhoto, CharityPhotoTranslation
from src.modules.charity_photos.models_dto import CharityPhotoResponseDTO
from tests.helpers.functions import random_string
from tests.modules.charity_photos.fixtures.models_dto import (
    CreateCharityPhotoFixtureDTO,
)


async def create_charity_photo_factory(
    session_db: AsyncSession,
    config_fix: Config,
    new_photo: CreateCharityPhotoFixtureDTO = CreateCharityPhotoFixtureDTO(),
) -> CharityPhotoResponseDTO:
    image_url = (
        new_photo.image_url
        if new_photo.image_url is not None
        else f"/{config_fix.paths.media.name}/{config_fix.paths.charity_photos.name}/{random_string()}.webp"
    )
    title = new_photo.title if new_photo.title is not None else f"Charity {random_string()}"
    description = (
        new_photo.description
        if new_photo.description is not None
        else f"Description {random_string()}"
    )
    index = new_photo.index if new_photo.index is not None else 0
    is_active = new_photo.is_active if new_photo.is_active is not None else True

    photo = CharityPhoto(
        image_url=image_url,
        index=index,
        is_active=is_active,
    )
    if title or description:
        photo.translations.append(
            CharityPhotoTranslation(
                locale=Language.ENG,
                title=title,
                description=description,
            )
        )
    session_db.add(photo)
    await session_db.commit()
    await session_db.refresh(photo)

    return CharityPhotoResponseDTO.model_validate(photo)
