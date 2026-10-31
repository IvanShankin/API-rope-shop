from typing import Optional

from fastapi import APIRouter, Depends, status

from src.modules.check_permission.depends import get_current_admin
from src.modules.notifications.depends import get_notification_service
from src.modules.notifications.models_dto import (
    TestEmailNotificationRequestDTO,
    TestNotificationResponseDTO,
    TestTelegramNotificationRequestDTO,
)
from src.modules.notifications.service import NotificationService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "/test/telegram",
    response_model=TestNotificationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Проверить отправку сообщения в Telegram (только админ)",
    description="Отправляет тестовое сообщение в Telegram, используя параметры из настроек сайта.",
)
async def test_telegram_notification(
    data: Optional[TestTelegramNotificationRequestDTO] = None,
    service: NotificationService = Depends(get_notification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> TestNotificationResponseDTO:
    chat_id = data.chat_id if data else None
    return await service.send_test_telegram(chat_id=chat_id)



@router.post(
    "/test/email",
    response_model=TestNotificationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Проверить отправку сообщения на Email (только админ)",
    description="Отправляет тестовое email-сообщение, используя параметры из настроек сайта.",
)
async def test_email_notification(
    data: Optional[TestEmailNotificationRequestDTO] = None,
    service: NotificationService = Depends(get_notification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> TestNotificationResponseDTO:
    to_email = data.to_email if data else None
    return await service.send_test_email(to_email=to_email)


