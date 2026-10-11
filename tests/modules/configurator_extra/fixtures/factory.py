from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.configurator_extra.fixtures.models_dto import (
    CreateConfiguratorExtraFixtureDTO,
    CreateConfiguratorExtraTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.configurator_setting.models import Currency
from src.modules.configurator_extra.models import (
    ConfiguratorExtra,
    ConfiguratorExtraTranslation,
    BillingType,
)
from src.modules.configurator_extra.models_dto import (
    ConfiguratorExtraResponseDTO,
    ConfiguratorExtraTranslationResponseDTO,
)


async def create_configurator_extra_factory(
    session_db: AsyncSession,
    new_extra: CreateConfiguratorExtraFixtureDTO = CreateConfiguratorExtraFixtureDTO(),
) -> ConfiguratorExtraResponseDTO:
    if new_extra.index is None:
        stmt = select(func.coalesce(func.max(ConfiguratorExtra.index), 0))
        max_idx = (await session_db.execute(stmt)).scalar_one()
        index = max_idx + 1
    else:
        index = new_extra.index

    extra = ConfiguratorExtra(
        code=random_string() if new_extra.code is None else new_extra.code,
        price=15.00 if new_extra.price is None else new_extra.price,
        currency=new_extra.currency if new_extra.currency is not None else Currency.EUR,
        billing_type=new_extra.billing_type if new_extra.billing_type is not None else BillingType.FIXED,
        index=index,
        is_active=True if new_extra.is_active is None else new_extra.is_active,
    )
    session_db.add(extra)
    await session_db.flush()

    # Создаем дефолтный перевод (ENG)
    trans = ConfiguratorExtraTranslation(
        extra_id=extra.id,
        locale=new_extra.locale if new_extra.locale is not None else Language.ENG,
        name=new_extra.name if new_extra.name is not None else random_string(),
        description=new_extra.description,
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(ConfiguratorExtra)
        .options(selectinload(ConfiguratorExtra.translations))
        .where(ConfiguratorExtra.id == extra.id)
    )
    loaded_extra = result.scalar_one()

    return ConfiguratorExtraResponseDTO.model_validate(loaded_extra)


async def create_configurator_extra_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateConfiguratorExtraTranslationFixtureDTO = CreateConfiguratorExtraTranslationFixtureDTO(),
) -> ConfiguratorExtraTranslationResponseDTO:
    if new_trans.extra_id is None:
        extra_dto = await create_configurator_extra_factory(session_db=session_db)
        extra_id = extra_dto.id
    else:
        extra_id = new_trans.extra_id

    trans = ConfiguratorExtraTranslation(
        extra_id=extra_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
        description=new_trans.description,
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return ConfiguratorExtraTranslationResponseDTO.model_validate(trans)
