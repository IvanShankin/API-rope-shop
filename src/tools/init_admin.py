import asyncio
import logging
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.config.config import AdminConfig
from src.modules.refresh_tokens.models import RefreshToken
from src.modules.users.models import User, UserRole

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("init_admin")


async def init_admin(
    session: Optional[AsyncSession] = None,
    config: Optional[Config] = None,
    cr_context: Optional[CryptContext] = None,
) -> User:
    """
    Инициализирует единственного администратора на основе настроек из конфигурации (.env).
    Если администраторы уже существуют, ничего не создаёт.
    Если нет, то создаётся единственный администратор.

    :param session: Опциональная асинхронная сессия SQLAlchemy.
    :param config: Опциональный объект конфигурации Config.
    :param cr_context: Опциональный контекст хеширования CryptContext.
    :return: Созданный объект User (администратор).
    """
    conf = config or Config()
    crypto = cr_context or CryptContext(schemes=["bcrypt"], deprecated="auto")

    if session is not None:
        return await _recreate_admin_if_needed(
            session=session,
            admin_config=conf.admin,
            cr_context=crypto,
        )

    async_session_factory = conf.db_connection.session_local
    async with async_session_factory() as local_session:
        return await _recreate_admin_if_needed(
            session=local_session,
            admin_config=conf.admin,
            cr_context=crypto,
        )


async def _recreate_admin_if_needed(
    session: AsyncSession,
    admin_config: AdminConfig,
    cr_context: CryptContext,
) -> User:
    """
    Проверяет наличие администраторов (или пользователей с конфликтующим email/username).
    При наличии ничего не делает.
    Если их нет, то создаёт единственного администратора с учётными данными из конфигурации.
    """
    stmt = select(User).where(
        or_(
            User.role == UserRole.ADMIN,
            User.email == admin_config.email,
            User.username == admin_config.username,
        )
    )
    existing_users = (await session.execute(stmt)).scalars().all()

    if existing_users:
        logger.info("The admin has been found; a new one will not be created.")
        return existing_users[0]
    else:
        logger.info("No existing admin found. Creating new admin...")

    admin = User(
        email=admin_config.email,
        username=admin_config.username,
        role=UserRole.ADMIN,
        hashed_password=cr_context.hash(admin_config.password),
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    logger.info(
        f"Admin initialized successfully: id={admin.id}, email='{admin.email}', username='{admin.username}'."
    )
    return admin


def main() -> None:
    """Точка входа при вызове скрипта из консоли."""
    asyncio.run(init_admin())


if __name__ == "__main__":
    main()
