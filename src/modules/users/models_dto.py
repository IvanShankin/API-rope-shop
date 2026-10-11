from datetime import datetime

from pydantic import EmailStr, BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO
from src.modules.users.models import UserRole


class UserDTO(ORMDTO):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserResponse(ORMDTO):
    id: int
    email: EmailStr
    username: str
    created_at: datetime


class RegisterUserRequestDTO(BaseModel):
    email: EmailStr
    username: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class CreateUserDTO(BaseModel):
    email: str
    username: str
    hashed_password: str