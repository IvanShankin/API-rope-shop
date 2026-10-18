from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.colors.repository import ColorRepository
from src.modules.rope_products.repository import RopeProductRepository, ProductVariantRepository
from src.modules.splice_materials.repository import SpliceMaterialRepository
from src.modules.splice_prices.repository import SplicePriceRuleRepository
from src.modules.splice_types.repository import SpliceTypeRepository
from src.modules.configurator_extra.repository import ConfiguratorExtraRepository
from src.modules.configurator_setting.repository import ConfiguratorSettingRepository
from src.modules.quote_requests.repository import (
    QuoteRequestRepository,
    QuoteRopeItemRepository,
    QuoteServiceItemRepository,
    QuoteExtraItemRepository,
)
from src.modules.quote_requests.service import QuoteRequestService


def get_quote_request_repository(
    session: AsyncSession = Depends(get_db),
) -> QuoteRequestRepository:
    return QuoteRequestRepository(session=session)


def get_quote_rope_item_repository(
    session: AsyncSession = Depends(get_db),
) -> QuoteRopeItemRepository:
    return QuoteRopeItemRepository(session=session)


def get_quote_service_item_repository(
    session: AsyncSession = Depends(get_db),
) -> QuoteServiceItemRepository:
    return QuoteServiceItemRepository(session=session)


def get_quote_extra_item_repository(
    session: AsyncSession = Depends(get_db),
) -> QuoteExtraItemRepository:
    return QuoteExtraItemRepository(session=session)


def get_quote_request_service(
    session: AsyncSession = Depends(get_db),
) -> QuoteRequestService:
    return QuoteRequestService(
        quote_repo=QuoteRequestRepository(session=session),
        rope_item_repo=QuoteRopeItemRepository(session=session),
        service_item_repo=QuoteServiceItemRepository(session=session),
        extra_item_repo=QuoteExtraItemRepository(session=session),
        rope_product_repo=RopeProductRepository(session=session),
        variant_repo=ProductVariantRepository(session=session),
        color_repo=ColorRepository(session=session),
        splice_type_repo=SpliceTypeRepository(session=session),
        splice_material_repo=SpliceMaterialRepository(session=session),
        splice_price_repo=SplicePriceRuleRepository(session=session),
        extra_repo=ConfiguratorExtraRepository(session=session),
        configurator_setting_repo=ConfiguratorSettingRepository(session=session),
        session=session,
    )
