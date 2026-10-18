from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.quote_requests.models import (
    ConfiguratorType,
    QuoteRequestStatus,
)
from src.modules.quote_requests.models_dto import (
    QuoteRequestCreate,
    QuoteRequestUpdateDTO,
    QuoteRequestUpdateStatusDTO,
    QuoteRequestResponseDTO,
    QuoteRequestListResponseDTO,
    QuoteRequestSortBy,
    SortOrder,
)
from src.modules.quote_requests.service import QuoteRequestService
from src.modules.quote_requests.depends import get_quote_request_service

router = APIRouter(prefix="/quote_requests", tags=["Quote Requests"])


@router.post(
    "",
    response_model=QuoteRequestResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_quote_request(
    data: QuoteRequestCreate,
    service: QuoteRequestService = Depends(get_quote_request_service),
):
    """
    Submit a new quote request from any configurator_extra (public).
    Snapshots and prices are automatically resolved and calculated by backend.
    """
    return await service.create_quote_request(data=data)


@router.get(
    "",
    response_model=QuoteRequestListResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def list_quote_requests(
    status_filter: Optional[QuoteRequestStatus] = Query(None, alias="status", description="Filter by status"),
    configurator_type: Optional[ConfiguratorType] = Query(None, description="Filter by configurator_extra type"),
    name: Optional[str] = Query(None, description="Filter by customer name (partial)"),
    email: Optional[str] = Query(None, description="Filter by email (partial)"),
    phone: Optional[str] = Query(None, description="Filter by phone (partial)"),
    request_number: Optional[str] = Query(None, description="Filter by request number (partial)"),
    is_urgent: Optional[bool] = Query(None, description="Filter by urgency flag"),
    created_from: Optional[datetime] = Query(None, description="Filter created on or after this timestamp"),
    created_to: Optional[datetime] = Query(None, description="Filter created on or before this timestamp"),
    search: Optional[str] = Query(None, description="Search text in number, name, email, phone"),
    sort_by: QuoteRequestSortBy = Query(
        QuoteRequestSortBy.CREATED_AT,
        description="Field to sort by (created_at, updated_at, total_price, request_number, status)",
    ),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order: 'asc' or 'desc'"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit for pagination"),
    service: QuoteRequestService = Depends(get_quote_request_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """List quote requests with advanced filters, search, and sorting (admin only)."""
    return await service.list_quote_requests(
        status=status_filter,
        configurator_type=configurator_type,
        name=name,
        email=email,
        phone=phone,
        request_number=request_number,
        is_urgent=is_urgent,
        created_from=created_from,
        created_to=created_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/number/{request_number}",
    response_model=QuoteRequestResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_quote_request_by_number(
    request_number: str,
    service: QuoteRequestService = Depends(get_quote_request_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Get quote request details by business request number (public)."""
    return await service.get_by_request_number(request_number=request_number)


@router.get(
    "/{id}",
    response_model=QuoteRequestResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_quote_request(
    id: int,
    service: QuoteRequestService = Depends(get_quote_request_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Get full quote request details with all items (admin only)."""
    return await service.get_quote_request_by_id(request_id=id)


@router.patch(
    "/{id}",
    response_model=QuoteRequestResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_quote_request(
    id: int,
    data: QuoteRequestUpdateDTO,
    service: QuoteRequestService = Depends(get_quote_request_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update quote request properties by admin (admin only)."""
    return await service.update_quote_request(request_id=id, data=data)


@router.patch(
    "/{id}/status",
    response_model=QuoteRequestResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_quote_request_status(
    id: int,
    data: QuoteRequestUpdateStatusDTO,
    service: QuoteRequestService = Depends(get_quote_request_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Change status of a quote request (admin only)."""
    return await service.update_quote_request_status(request_id=id, status=data.status)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_quote_request(
    id: int,
    service: QuoteRequestService = Depends(get_quote_request_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete a quote request and its items (admin only)."""
    await service.delete_quote_request(request_id=id)
