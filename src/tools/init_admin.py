import asyncio
import logging
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.config.config import AdminConfig
import src.modules.db_models  # noqa: F401 - ensure all ORM models are registered
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
) -> Optional[User]:
    """
    Инициализирует администратора на основе настроек из конфигурации (.env).
    Создаёт администратора только при его отсутствии, без удаления существующих учётных записей.
    Если администратор уже существует в системе, создание пропускается.

    :param session: Опциональная асинхронная сессия SQLAlchemy.
    :param config: Опциональный объект конфигурации Config.
    :param cr_context: Опциональный контекст хеширования CryptContext.
    :return: Созданный или уже существующий объект User (администратор).
    """
    conf = config or Config()
    crypto = cr_context or CryptContext(schemes=["bcrypt"], deprecated="auto")

    if session is not None:
        return await _create_admin_if_not_exists(
            session=session,
            admin_config=conf.admin,
            cr_context=crypto,
        )

    async_session_factory = conf.db_connection.session_local
    async with async_session_factory() as local_session:
        return await _create_admin_if_not_exists(
            session=local_session,
            admin_config=conf.admin,
            cr_context=crypto,
        )


async def _create_admin_if_not_exists(
    session: AsyncSession,
    admin_config: AdminConfig,
    cr_context: CryptContext,
) -> Optional[User]:
    """
    Проверяет наличие администратора в БД.
    Если пользователь с ролью ADMIN уже есть, пропускает создание.
    Если администратора нет:
      - если уже есть пользователь с совпадающим email или username, обновляет его роль до ADMIN.
      - иначе создаёт нового администратора без удаления каких-либо существующих учётных записей.
    """
    # 1. Проверяем, существует ли уже хотя бы один администратор
    stmt_admin = select(User).where(User.role == UserRole.ADMIN).limit(1)
    existing_admin = (await session.execute(stmt_admin)).scalar_one_or_none()

    if existing_admin is not None:
        logger.info(
            f"Admin already exists (id={existing_admin.id}, username='{existing_admin.username}'). "
            "Skipping creation."
        )
        return existing_admin

    # 2. Администратора нет. Проверяем, есть ли пользователь с совпадающим email или username
    stmt_conflicting = select(User).where(
        or_(
            User.email == admin_config.email,
            User.username == admin_config.username,
        )
    ).limit(1)
    existing_user = (await session.execute(stmt_conflicting)).scalar_one_or_none()

    if existing_user is not None:
        logger.info(
            f"User with matching credentials found (id={existing_user.id}, username='{existing_user.username}'). "
            "Promoting to ADMIN without deleting account..."
        )
        existing_user.role = UserRole.ADMIN
        await session.commit()
        await session.refresh(existing_user)
        return existing_user

    # 3. Создаём нового администратора
    if not admin_config.password:
        logger.warning("Admin creation skipped: no admin password configured in environment.")
        return None

    logger.info("No admin found in database. Creating initial admin...")
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
