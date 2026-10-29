from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import Base


class Settings(Base):
    """
    Системные настройки магазина (Singleton - ровно одна запись).
    Позволяет администратору управлять каналами уведомлений и контактной информацией
    через API / админку без необходимости перезапуска сервиса и правки .env.
    """
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Telegram уведомления менеджерам
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telegram_notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Email уведомления
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    manager_notification_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    manager_email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Общие данные магазина / контакты
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Rope Shop")
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default="info@ropeshop.com")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="+1 (555) 019-2834")
    site_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default="https://ropeshop.com")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
