from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from src.modules.base.database_model import DEFAULT_LOCALE, Language
from src.modules.quote_requests.models import ConfiguratorType
from src.modules.configurators.models_dto import (
    ConfiguratorDataResponseDTO,
    SplicePriceCalculationResponseDTO,
)
from src.modules.configurators.service import ConfiguratorService
from src.modules.configurators.depends import get_configurators_service


router = APIRouter(prefix="/configurators", tags=["Configurators"])


@router.get(
    "",
    response_model=ConfiguratorDataResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get unified configurator settings and catalog data",
    description=(
        "Returns aggregated initialization data for frontend configurators "
        "(global settings, active extras, tariff groups, splice types, price rules, and rope catalog). "
        "Supports filtering by configurator_type (rope_with_splice, loop_only, splice_only) and locale."
    ),
)
async def get_configurator_data(
    configurator_type: Optional[ConfiguratorType] = Query(
        None,
        description="Optional filter by configurator type. If omitted, returns combined data for all configurators.",
    ),
    locale: Language = Query(
        DEFAULT_LOCALE,
        description="Target language for translated fields (name, description). Defaults to eng.",
    ),
    service: ConfiguratorService = Depends(get_configurators_service),
) -> ConfiguratorDataResponseDTO:
    return await service.get_configurator_data(
        configurator_type=configurator_type,
        locale=locale,
    )


@router.get(
    "/price",
    response_model=SplicePriceCalculationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Calculate splice price by material, type and diameter",
    description=(
        "Calculates exact price for a splice operation based on material group, splice type, and diameter (mm). "
        "Allows frontend to query individual prices dynamically if client-side matrix evaluation is not preferred."
    ),
)
async def calculate_splice_price(
    material_id: int = Query(..., description="ID материала (тарифной группы заделки)"),
    splice_type_id: int = Query(..., description="ID типа заделки"),
    diameter_mm: float = Query(..., gt=0, description="Диаметр каната в мм"),
    service: ConfiguratorService = Depends(get_configurators_service),
) -> SplicePriceCalculationResponseDTO:
    return await service.calculate_splice_price(
        material_id=material_id,
        splice_type_id=splice_type_id,
        diameter_mm=diameter_mm,
    )

