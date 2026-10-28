from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.check_permission.depends import get_current_admin, get_optional_admin
from src.modules.users.models_dto import UserDTO
from src.modules.splice_materials.models_dto import (
    SpliceMaterialDependenciesDTO,
    SpliceMaterialResponseDTO,
    SpliceMaterialCreate,
    SpliceMaterialUpdate
)
from src.modules.splice_materials.service import SpliceMaterialService
from src.modules.splice_materials.depends import get_splice_material_service

router = APIRouter(prefix="/splice_materials", tags=["Splice Materials"])


@router.get(
    "", 
    response_model=List[SpliceMaterialResponseDTO], 
    status_code=status.HTTP_200_OK
)
async def get_all_splice_materials(
    include_rules: bool = Query(False, description="Include nested price rules in the response"),
    service: SpliceMaterialService = Depends(get_splice_material_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
) -> List[SpliceMaterialResponseDTO]:
    """Get all splice materials (public)."""
    return await service.get_all_materials(include_rules=include_rules, is_admin=admin is not None)


@router.get(
    "/{material_id}", 
    response_model=SpliceMaterialResponseDTO, 
    status_code=status.HTTP_200_OK
)
async def get_splice_material(
    material_id: int,
    include_rules: bool = Query(False, description="Include nested price rules in the response"),
    service: SpliceMaterialService = Depends(get_splice_material_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
) -> SpliceMaterialResponseDTO:
    """Get splice material by ID (public)."""
    return await service.get_material_by_id(material_id, include_rules=include_rules, is_admin=admin is not None)


@router.post("", response_model=SpliceMaterialResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_splice_material(
    data: SpliceMaterialCreate,
    service: SpliceMaterialService = Depends(get_splice_material_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Create a new splice material (admin only)."""
    return await service.create_material(data)


@router.patch("/{material_id}", response_model=SpliceMaterialResponseDTO, status_code=status.HTTP_200_OK)
async def update_splice_material(
    material_id: int,
    data: SpliceMaterialUpdate,
    service: SpliceMaterialService = Depends(get_splice_material_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Update a splice material (admin only)."""
    return await service.update_material(material_id, data)


@router.get(
    "/{material_id}/dependencies",
    response_model=SpliceMaterialDependenciesDTO,
    status_code=status.HTTP_200_OK,
    summary="Get splice material dependencies",
    description="Get count and list of linked price rules and rope products before deletion (admin only).",
)
async def get_splice_material_dependencies(
    material_id: int,
    service: SpliceMaterialService = Depends(get_splice_material_service),
    admin: UserDTO = Depends(get_current_admin),
) -> SpliceMaterialDependenciesDTO:
    """Get splice material dependencies before deletion (admin only)."""
    return await service.get_dependencies(material_id)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_splice_material(
    material_id: int,
    service: SpliceMaterialService = Depends(get_splice_material_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Delete a splice material (admin only)."""
    await service.delete_material(material_id)
