from typing import Optional

from pydantic import BaseModel


class CreateContactRequestFixtureDTO(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
