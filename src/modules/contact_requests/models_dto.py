from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.modules.base.orm_dto import ORMDTO


class ContactRequestBaseDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Contact name / entity")
    email: str = Field(..., min_length=1, max_length=255, description="Contact email address")
    phone: Optional[str] = Field(None, max_length=100, description="Contact phone number")
    message: Optional[str] = Field(None, description="Contact form message / text")


class ContactRequestCreateDTO(ContactRequestBaseDTO):
    pass


class ContactRequestUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Contact name / entity")
    email: Optional[str] = Field(None, min_length=1, max_length=255, description="Contact email address")
    phone: Optional[str] = Field(None, max_length=100, description="Contact phone number")
    message: Optional[str] = Field(None, description="Contact form message / text")


class ContactRequestResponseDTO(ContactRequestBaseDTO, ORMDTO):
    id: int
    created_at: datetime
