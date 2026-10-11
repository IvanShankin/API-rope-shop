from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from src.modules.users.models import User, UserRole
from src.modules.users.models_dto import UserDTO

def _get_hash_password(crypto_context: CryptContext, password: str) -> str:
    return crypto_context.hash(password)

async def create_user_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_user: CreateUserFixtureDTO = CreateUserFixtureDTO(),
) -> UserDTO:
    user = User(
        email=random_string() + "@mail.com" if new_user.email is None else new_user.email,
        username=random_string() if new_user.username is None else new_user.username,
        role=new_user.role if new_user.role else UserRole.USER,
        hashed_password=_get_hash_password(
            crypto_context=crypto_context,
            password=random_string() if new_user.password is None else new_user.password
        )
    )
    session_db.add(user)
    await session_db.commit()
    await session_db.refresh(user)

    return UserDTO.model_validate(user)
