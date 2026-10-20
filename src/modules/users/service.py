from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import ServiceException
from src.modules.users.exception import (
    UserAlreadyExists,
    UserAlreadyExit,
    UserNotFound,
    IncorrectPassword,
)
from src.modules.users.models_dto import (
    UserDTO,
    RegisterUserRequestDTO,
    CreateUserDTO,
    ChangePasswordDTO,
)
from src.modules.users.repository import UsersRepository


class UsersService:

    def __init__(
        self,
        users_repo: UsersRepository,
        cr_context: CryptContext,
        session_db: AsyncSession,
    ):
        self.users_repo = users_repo
        self.cr_context = cr_context
        self.session_db = session_db

    def _get_hash_password(self, password: str) -> str:
        """Преобразует пароль в хеш
        :return: хэш пароля"""
        return self.cr_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Проверяет, совпадает ли пароль с хешем
        :param plain_password: простой пароль (qwerty)
        :param hashed_password: хэш пароля (gfdjkjvzvxccxa)
        :return: результат совпадения
        """
        return self.cr_context.verify(plain_password, hashed_password)

    async def get_user_by_username_or_email(self, username_or_email: str) -> UserDTO | None:
        result = await self.users_repo.get_user_by_username_or_email(username_or_email)
        return UserDTO.model_validate(result) if result else None

    async def get_user_by_id(self, user_id: int) -> UserDTO | None:
        result = await self.users_repo.get_user_by_id(user_id)
        return UserDTO.model_validate(result) if result else None

    async def get_user_by_email(self, email: str) -> UserDTO | None:
        result = await self.users_repo.get_user_by_email(email)
        return UserDTO.model_validate(result) if result else None

    async def get_user_by_username(self, username: str) -> UserDTO | None:
        result = await self.users_repo.get_user_by_username(username)
        return UserDTO.model_validate(result) if result else None

    async def create_user(
        self,
        new_user: RegisterUserRequestDTO
    ) -> UserDTO:
        """
        :raises UserAlreadyExists:
        """
        if (
            await self.users_repo.get_user_by_email(new_user.email)
            or await self.users_repo.get_user_by_username(new_user.username)
        ):
            raise UserAlreadyExists()

        hashed_password = self._get_hash_password(new_user.password)

        try:
            result = await self.users_repo.add_user(
                data=CreateUserDTO(
                    email=new_user.email,
                    username=new_user.username,
                    hashed_password=hashed_password,
                )
            )
            await self.session_db.commit()
            await self.session_db.refresh(result)
        except IntegrityError as e:
            await self.session_db.rollback()
            raise UserAlreadyExists() from e
        except Exception as e:
            await self.session_db.rollback()
            raise ServiceException(str(e)) from e

        return UserDTO.model_validate(result)

    async def change_password(
        self,
        user_id: int,
        data: ChangePasswordDTO,
    ) -> None:
        """
        Смена пароля пользователя.
        :raises UserNotFound: если пользователь не найден
        :raises IncorrectPassword: если текущий пароль неверен
        """
        user = await self.users_repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFound()

        if not self.verify_password(data.current_password, user.hashed_password):
            raise IncorrectPassword("Incorrect current password")

        new_hashed_password = self._get_hash_password(data.new_password)
        try:
            await self.users_repo.update_password(user_id, new_hashed_password)
            await self.session_db.commit()
        except Exception as e:
            await self.session_db.rollback()
            raise ServiceException(str(e)) from e
