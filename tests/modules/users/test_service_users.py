import pytest
from tests.helpers import test_crypto_context
from src.modules.users.models_dto import RegisterUserRequestDTO
from src.modules.users.repository import UsersRepository
from src.modules.users.service import UsersService
from src.modules.users.exception import UserAlreadyExists, UserAlreadyExit


@pytest.mark.asyncio
async def test_create_user_success(session_db):
    repo = UsersRepository(session=session_db)
    service = UsersService(
        users_repo=repo,
        cr_context=test_crypto_context,
        session_db=session_db,
    )

    request_dto = RegisterUserRequestDTO(
        email="new_test_user@example.com",
        username="new_test_username",
        password="secret_password123",
    )

    created_user = await service.create_user(request_dto)
    assert created_user.id is not None
    assert created_user.email == request_dto.email
    assert created_user.username == request_dto.username


@pytest.mark.asyncio
async def test_create_user_duplicate_email_raises(session_db):
    repo = UsersRepository(session=session_db)
    service = UsersService(
        users_repo=repo,
        cr_context=test_crypto_context,
        session_db=session_db,
    )

    await service.create_user(
        RegisterUserRequestDTO(
            email="duplicate_email@example.com",
            username="unique_user_1",
            password="secret_password123",
        )
    )

    with pytest.raises(UserAlreadyExists) as exc_info:
        await service.create_user(
            RegisterUserRequestDTO(
                email="duplicate_email@example.com",
                username="unique_user_2",
                password="secret_password123",
            )
        )
    # Check backward compatibility alias
    assert isinstance(exc_info.value, UserAlreadyExit)


@pytest.mark.asyncio
async def test_create_user_duplicate_username_raises(session_db):
    repo = UsersRepository(session=session_db)
    service = UsersService(
        users_repo=repo,
        cr_context=test_crypto_context,
        session_db=session_db,
    )

    await service.create_user(
        RegisterUserRequestDTO(
            email="unique_email_1@example.com",
            username="same_username",
            password="secret_password123",
        )
    )

    with pytest.raises(UserAlreadyExists) as exc_info:
        await service.create_user(
            RegisterUserRequestDTO(
                email="unique_email_2@example.com",
                username="same_username",
                password="secret_password123",
            )
        )
    assert isinstance(exc_info.value, UserAlreadyExit)
