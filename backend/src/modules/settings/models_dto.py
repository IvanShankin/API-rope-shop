from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.modules.base.orm_dto import ORMDTO


class SettingsResponseDTO(ORMDTO):
    id: int
    telegram_chat_id: Optional[str] = None
    telegram_notifications_enabled: bool = True
    email_notifications_enabled: bool = True
    manager_notification_email: Optional[str] = None
    manager_email_notifications_enabled: bool = False
    company_name: str = "Rope Shop"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    site_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SettingsPublicResponseDTO(ORMDTO):
    company_name: str = "Rope Shop"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    site_url: Optional[str] = None


class SettingsUpdateDTO(BaseModel):
    telegram_chat_id: Optional[str] = None
    telegram_notifications_enabled: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    manager_notification_email: Optional[str] = None
    manager_email_notifications_enabled: Optional[bool] = None
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    site_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
