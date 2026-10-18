from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.splice_prices.models_dto import (
    SplicePriceRuleResponseDTO,
    SplicePriceRuleWithRelationsResponseDTO,
    SplicePriceRuleCreate,
    SplicePriceRuleUpdate
)
from src.modules.splice_prices.service import SplicePriceRuleService
from src.modules.splice_prices.depends import get_splice_price_service

router = APIRouter(prefix="/splice_prices", tags=["Splice Price Rules"])

@router.get("", response_model=List[SplicePriceRuleWithRelationsResponseDTO], status_code=status.HTTP_200_OK)
async def get_all_rules(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: SplicePriceRuleService = Depends(get_splice_price_service)
):
    return await service.get_all_rules(is_active=is_active)

@router.get("/applicable", response_model=List[SplicePriceRuleWithRelationsResponseDTO], status_code=status.HTTP_200_OK)
async def get_applicable_rules(
    material_id: int = Query(..., description="ID of the splice material"),
    diameter: float = Query(..., description="Diameter of the rope in mm"),
    splice_type_ids: Optional[List[int]] = Query(None, description="List of allowed splice type IDs"),
    service: SplicePriceRuleService = Depends(get_splice_price_service)
):
    return await service.get_applicable_rules(
        material_id=material_id, 
        diameter=diameter, 
        splice_type_ids=splice_type_ids
    )

@router.get("/{rule_id}", response_model=SplicePriceRuleWithRelationsResponseDTO, status_code=status.HTTP_200_OK)
async def get_rule(
    rule_id: int,
    service: SplicePriceRuleService = Depends(get_splice_price_service)
):
    return await service.get_rule_by_id(rule_id)

@router.post("", response_model=SplicePriceRuleResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: SplicePriceRuleCreate,
    service: SplicePriceRuleService = Depends(get_splice_price_service),
    admin: UserDTO = Depends(get_current_admin)
):
    return await service.create_rule(data)

@router.patch("/{rule_id}", response_model=SplicePriceRuleResponseDTO, status_code=status.HTTP_200_OK)
async def update_rule(
    rule_id: int,
    data: SplicePriceRuleUpdate,
    service: SplicePriceRuleService = Depends(get_splice_price_service),
    admin: UserDTO = Depends(get_current_admin)
):
    return await service.update_rule(rule_id, data)

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    service: SplicePriceRuleService = Depends(get_splice_price_service),
    admin: UserDTO = Depends(get_current_admin)
):
    await service.delete_rule(rule_id)
