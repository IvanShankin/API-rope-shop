from fastapi import APIRouter, Depends, Request, status

from src.core.rate_limit import limiter
from src.modules.check_permission.depends import get_current_admin
from src.modules.contact_requests.depends import get_contact_request_service
from src.modules.contact_requests.models_dto import (
    ContactRequestCreateDTO,
    ContactRequestResponseDTO,
    ContactRequestUpdateDTO,
)
from src.modules.contact_requests.service import ContactRequestService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/contact_requests", tags=["Contact Requests"])


@router.post(
    "",
    response_model=ContactRequestResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Submit contact form request",
    description="Submit an incoming inquiry / contact form message (public access).",
)
@limiter.limit("5/minute")
async def create_contact_request(
    request: Request,
    data: ContactRequestCreateDTO,
    service: ContactRequestService = Depends(get_contact_request_service),
) -> ContactRequestResponseDTO:
    return await service.create_contact(data=data)


@router.get(
    "",
    response_model=ContactRequestResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get contact form info",
    description="Get general contact form information (public access).",
)
async def get_contact_info(
    service: ContactRequestService = Depends(get_contact_request_service),
) -> ContactRequestResponseDTO:
    return await service.get_contact()


@router.patch(
    "",
    response_model=ContactRequestResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update contact form info",
    description="Update general contact form information (admin only).",
)
async def update_contact_info(
    data: ContactRequestUpdateDTO,
    service: ContactRequestService = Depends(get_contact_request_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ContactRequestResponseDTO:
    return await service.update_contact(data=data)


@router.get(
    "/{request_id}",
    response_model=ContactRequestResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get contact form info by ID",
    description="Get contact form information by ID (public access).",
)
async def get_contact_info_by_id(
    request_id: int,
    service: ContactRequestService = Depends(get_contact_request_service),
) -> ContactRequestResponseDTO:
    return await service.get_contact_by_id(contact_id=request_id)


@router.patch(
    "/{request_id}",
    response_model=ContactRequestResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update contact form info by ID",
    description="Update contact form information by ID (admin only).",
)
async def update_contact_info_by_id(
    request_id: int,
    data: ContactRequestUpdateDTO,
    service: ContactRequestService = Depends(get_contact_request_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ContactRequestResponseDTO:
    return await service.update_contact_by_id(contact_id=request_id, data=data)
