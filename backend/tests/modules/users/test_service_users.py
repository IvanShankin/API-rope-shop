import pytest
from tests.helpers import test_crypto_context
from src.modules.users.models_dto import RegisterUserRequestDTO, ChangePasswordDTO
from src.modules.users.repository import UsersRepository
from src.modules.users.service import UsersService
from src.modules.users.exception import (
    UserAlreadyExists,
    UserAlreadyExit,
    IncorrectPassword,
    UserNotFound,
)


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


@pytest.mark.asyncio
async def test_change_password_service_success(session_db):
    repo = UsersRepository(session=session_db)
    service = UsersService(
        users_repo=repo,
        cr_context=test_crypto_context,
        session_db=session_db,
    )

    user = await service.create_user(
        RegisterUserRequestDTO(
            email="change_pwd_user@example.com",
            username="change_pwd_user",
            password="old_password_123",
        )
    )

    await service.change_password(
        user_id=user.id,
        data=ChangePasswordDTO(
            current_password="old_password_123",
            new_password="new_password_456",
        ),
    )

    updated_user = await repo.get_user_by_id(user.id)
    assert service.verify_password("new_password_456", updated_user.hashed_password)
    assert not service.verify_password("old_password_123", updated_user.hashed_password)


@pytest.mark.asyncio
async def test_change_password_service_incorrect_password_raises(session_db):
    repo = UsersRepository(session=session_db)
    service = UsersService(
        users_repo=repo,
        cr_context=test_crypto_context,
        session_db=session_db,
    )

    user = await service.create_user(
        RegisterUserRequestDTO(
            email="change_pwd_err@example.com",
            username="change_pwd_err",
            password="correct_pwd",
        )
    )

    with pytest.raises(IncorrectPassword):
        await service.change_password(
            user_id=user.id,
            data=ChangePasswordDTO(
                current_password="wrong_pwd",
                new_password="new_password_456",
            ),
        )


@pytest.mark.asyncio
async def test_change_password_service_user_not_found_raises(session_db):
    repo = UsersRepository(session=session_db)
    service = UsersService(
        users_repo=repo,
        cr_context=test_crypto_context,
        session_db=session_db,
    )

    with pytest.raises(UserNotFound):
        await service.change_password(
            user_id=999999,
            data=ChangePasswordDTO(
                current_password="any_password",
                new_password="new_password_456",
            ),
        )
