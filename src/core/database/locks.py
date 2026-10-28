import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("database_locks")

# Константные 64-битные идентификаторы блокировок для pg_advisory_xact_lock
LOCK_ID_INIT_SETTINGS = 84729101
LOCK_ID_INIT_CONFIGURATOR_SETTING = 84729102
LOCK_ID_INIT_CONTACT_REQUEST = 84729103
LOCK_ID_INIT_ADMIN = 84729104


async def acquire_advisory_lock(session: AsyncSession, lock_id: int) -> None:
    """
    Захватывает транзакционную рекомендательную блокировку PostgreSQL (pg_advisory_xact_lock).
    Блокировка автоматически освобождается сервером PostgreSQL при завершении текущей
    транзакции (commit или rollback).
    Если СУБД не является PostgreSQL (например, при тестировании на SQLite), операция
    безопасно пропускается.
    """
    try:
        bind = session.get_bind()
        if bind and getattr(bind, "dialect", None) and bind.dialect.name == "postgresql":
            await session.execute(
                text("SELECT pg_advisory_xact_lock(:lock_id)"),
                {"lock_id": lock_id},
            )
    except Exception as e:
        logger.debug("Advisory lock skipped or unsupported: %s", e)
