import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.modules.contact_requests.models import ContactRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("init_contact_request")

DEFAULT_CONTACT_DATA = {
    "name": "General Contact",
    "email": "info@ropeshop.com",
    "phone": "+1 (555) 019-2834",
    "message": "Welcome to our rope shop. Feel free to contact us with any inquiries.",
}


async def init_contact_request(
    session: Optional[AsyncSession] = None,
    config: Optional[Config] = None,
) -> ContactRequest:
    """
    Создаёт начальную запись в таблице contact_requests при её отсутствии.
    Если запись уже есть, создание пропускается.

    :param session: Опциональная асинхронная сессия SQLAlchemy.
    :param config: Опциональный объект конфигурации Config.
    :return: Объект ContactRequest (созданный или уже существующий).
    """
    if session is not None:
        return await _create_contact_request_if_not_exists(session)

    conf = config or Config()
    async_session_factory = conf.db_connection.session_local
    async with async_session_factory() as local_session:
        return await _create_contact_request_if_not_exists(local_session)


async def _create_contact_request_if_not_exists(
    session: AsyncSession,
) -> ContactRequest:
    """
    Проверяет наличие хотя бы одной записи в таблице contact_requests.
    Если таблица пуста, создаёт запись со значениями по умолчанию.
    """
    stmt = select(ContactRequest).limit(1)
    result = await session.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact is None:
        logger.info("ContactRequest record not found. Creating default contact record...")
        contact = ContactRequest(**DEFAULT_CONTACT_DATA)
        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        logger.info(
            f"ContactRequest created successfully (id={contact.id}, name='{contact.name}', email='{contact.email}')."
        )
    else:
        logger.info(f"ContactRequest already exists (id={contact.id}). Skipping creation.")

    return contact


def main() -> None:
    """Точка входа при вызове скрипта из консоли."""
    asyncio.run(init_contact_request())


if __name__ == "__main__":
    main()
