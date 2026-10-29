from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.functions import random_string
from tests.modules.products.fixtures.factory import create_product_factory
from tests.modules.product_application.fixtures.models_dto import (
    CreateProductApplicationFixtureDTO,
    CreateProductApplicationTranslationFixtureDTO,
    CreateProductAssignedApplicationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.product_application.models import (
    ProductApplication,
    ProductApplicationTranslation,
    ProductAssignedApplication,
)
from src.modules.product_application.models_dto import (
    ProductApplicationLocalizedResponseDTO,
    ProductApplicationResponseDTO,
    ProductApplicationTranslationResponseDTO,
    ProductAssignedApplicationResponseDTO,
)


async def create_product_application_factory(
    session_db: AsyncSession,
    new_app: CreateProductApplicationFixtureDTO = CreateProductApplicationFixtureDTO(),
) -> ProductApplicationResponseDTO:
    app = ProductApplication(
        code=random_string(8) if new_app.code is None else new_app.code,
        index=0 if new_app.index is None else new_app.index,
        is_active=True if new_app.is_active is None else new_app.is_active,
    )
    session_db.add(app)
    await session_db.flush()

    # Default translation
    trans = ProductApplicationTranslation(
        application_id=app.id,
        locale=new_app.locale if new_app.locale is not None else Language.ENG,
        name=new_app.name if new_app.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(ProductApplication)
        .where(ProductApplication.id == app.id)
        .options(selectinload(ProductApplication.translations))
    )
    app = result.scalar_one()

    return ProductApplicationResponseDTO.model_validate(app)


async def create_product_application_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateProductApplicationTranslationFixtureDTO = CreateProductApplicationTranslationFixtureDTO(),
) -> ProductApplicationTranslationResponseDTO:
    if new_trans.application_id is None:
        app = await create_product_application_factory(session_db=session_db)
        application_id = app.id
    else:
        application_id = new_trans.application_id

    trans = ProductApplicationTranslation(
        application_id=application_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return ProductApplicationTranslationResponseDTO.model_validate(trans)


async def create_product_assigned_application_factory(
    session_db: AsyncSession,
    new_assign: CreateProductAssignedApplicationFixtureDTO = CreateProductAssignedApplicationFixtureDTO(),
) -> ProductAssignedApplicationResponseDTO:
    if new_assign.product_id is None:
        prod = await create_product_factory(session_db=session_db)
        product_id = prod.id
    else:
        product_id = new_assign.product_id

    if new_assign.application_id is None:
        app_dto = await create_product_application_factory(session_db=session_db)
        application_id = app_dto.id
    else:
        application_id = new_assign.application_id

    assigned = ProductAssignedApplication(
        product_id=product_id,
        application_id=application_id,
    )
    session_db.add(assigned)
    await session_db.commit()

    result = await session_db.execute(
        select(ProductAssignedApplication)
        .where(
            ProductAssignedApplication.product_id == product_id,
            ProductAssignedApplication.application_id == application_id,
        )
        .options(
            selectinload(ProductAssignedApplication.application).selectinload(
                ProductApplication.translations
            )
        )
    )
    assigned_obj = result.scalar_one()

    name = assigned_obj.application._get_field_with_translation(lambda t: t.name, Language.ENG) or ""
    localized_app = ProductApplicationLocalizedResponseDTO(
        id=assigned_obj.application.id,
        code=assigned_obj.application.code,
        index=assigned_obj.application.index,
        is_active=assigned_obj.application.is_active,
        name=name,
    )
    return ProductAssignedApplicationResponseDTO(
        product_id=product_id,
        application_id=application_id,
        application=localized_app,
    )
