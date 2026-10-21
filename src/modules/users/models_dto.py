from datetime import datetime
from typing import Any

from pydantic import EmailStr, BaseModel, ConfigDict, Field, model_validator

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
    role: UserRole


class RegisterUserRequestDTO(BaseModel):
    email: EmailStr
    username: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class CreateUserDTO(BaseModel):
    email: str
    username: str
    hashed_password: str


class ChangePasswordDTO(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)
    confirm_password: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "current_password" not in data and "old_password" in data:
                data["current_password"] = data["old_password"]
            if "confirm_password" not in data and "new_password_confirm" in data:
                data["confirm_password"] = data["new_password_confirm"]
        return data

    @model_validator(mode="after")
    def validate_password_match(self):
        if self.confirm_password is not None and self.confirm_password != self.new_password:
            raise ValueError("New password and confirmation do not match")
        return self


class ChangePasswordResponse(BaseModel):
    detail: str = "Password changed successfully"
    message: str = "Password changed successfully"
