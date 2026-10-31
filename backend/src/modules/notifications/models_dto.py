from typing import Optional

from pydantic import BaseModel, Field


class TestTelegramNotificationRequestDTO(BaseModel):
    __test__ = False
    chat_id: Optional[str] = Field(
        None,
        description="Опциональный chat_id для тестовой отправки (если не передан, берётся из настроек сайта)",
    )


class TestEmailNotificationRequestDTO(BaseModel):
    __test__ = False
    to_email: Optional[str] = Field(
        None,
        description="Опциональный email для тестовой отправки (если не передан, берётся из настроек сайта)",
    )


class TestNotificationResponseDTO(BaseModel):
    __test__ = False
    success: bool = Field(..., description="Флаг успешности отправки тестового уведомления")
    message: str = Field(..., description="Информационное сообщение или описание возникшей ошибки")
    target: Optional[str] = Field(None, description="Целевой chat_id или email адрес, куда выполнялась отправка")
