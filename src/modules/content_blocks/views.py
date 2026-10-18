from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.content_blocks.depends import (
    get_content_block_service,
    get_optional_admin,
)
from src.modules.content_blocks.models_dto import (
    ContentBlockResponseDTO,
    ContentBlockUpdateDTO,
)
from src.modules.content_blocks.service import ContentBlockService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/content_blocks", tags=["Content Blocks"])


@router.get(
    "/page/{page_code}",
    response_model=List[ContentBlockResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get content blocks by page code",
    description=(
        "Returns all content blocks for the specified page_code with eager loaded translations. "
        "Public users receive only active blocks (is_active=True). "
        "Admin can see all blocks and filter by is_active."
    ),
)
async def get_blocks_by_page_code(
    page_code: str,
    locale: Optional[Language] = Query(
        None, description="Preferred language for title and content"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status (admin only)"
    ),
    service: ContentBlockService = Depends(get_content_block_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
) -> List[ContentBlockResponseDTO]:
    is_admin = admin is not None
    return await service.get_blocks_by_page(
        page_code=page_code,
        locale=locale,
        is_active=is_active,
        is_admin=is_admin,
    )


@router.get(
    "",
    response_model=List[ContentBlockResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get content blocks by page_code query parameter",
    description="Alternative route to get blocks for a page using query parameter (?page_code=...).",
)
async def get_blocks_by_page_query(
    page_code: str = Query(..., description="Page identifier"),
    locale: Optional[Language] = Query(
        None, description="Preferred language for title and content"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status (admin only)"
    ),
    service: ContentBlockService = Depends(get_content_block_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
) -> List[ContentBlockResponseDTO]:
    is_admin = admin is not None
    return await service.get_blocks_by_page(
        page_code=page_code,
        locale=locale,
        is_active=is_active,
        is_admin=is_admin,
    )


@router.get(
    "/{block_code}",
    response_model=ContentBlockResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get single content block by block code",
    description=(
        "Returns a single content block by its unique block_code with all loaded translations. "
        "Public users can only view active blocks. Inactive blocks return 404 for public users."
    ),
)
async def get_block_by_code(
    block_code: str,
    locale: Optional[Language] = Query(
        None, description="Preferred language for title and content"
    ),
    service: ContentBlockService = Depends(get_content_block_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
) -> ContentBlockResponseDTO:
    is_admin = admin is not None
    return await service.get_block_by_code(
        block_code=block_code,
        locale=locale,
        is_admin=is_admin,
    )


@router.patch(
    "/{block_code}",
    response_model=ContentBlockResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update content block by block code (Admin only)",
    description=(
        "Updates block attributes and batch upserts translations for all specified languages in a single transaction. "
        "Admin only."
    ),
)
@router.put(
    "/{block_code}",
    response_model=ContentBlockResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update or create content block by block code (Admin only)",
    description=(
        "Updates or creates block and batch upserts translations for all specified languages in a single transaction. "
        "Admin only."
    ),
)
async def update_block_by_code(
    block_code: str,
    data: ContentBlockUpdateDTO,
    service: ContentBlockService = Depends(get_content_block_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ContentBlockResponseDTO:
    return await service.update_block_by_code(
        block_code=block_code,
        data=data,
    )
