from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.contact_requests.models import ContactRequest


class ContactRequestRepository(BaseRepository[ContactRequest]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ContactRequest)

    async def get_first(self) -> Optional[ContactRequest]:
        """Получение первой записи контактных данных."""
        stmt = select(ContactRequest).order_by(ContactRequest.id).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id(self, contact_id: int) -> Optional[ContactRequest]:
        """Получение записи контактных данных по ID."""
        stmt = select(ContactRequest).where(ContactRequest.id == contact_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def count(self) -> int:
        """Подсчет количества записей контактных данных."""
        stmt = select(func.count()).select_from(ContactRequest)
        res = await self.session.execute(stmt)
        return res.scalar_one() or 0

    def add_contact(self, obj: ContactRequest) -> ContactRequest:
        """Добавление сущности контактных данных в сессию."""
        self.session.add(obj)
        return obj

    async def update_contact(self, contact_id: int, values: dict) -> None:
        """Обновление полей контактных данных."""
        if not values:
            return
        stmt = (
            update(ContactRequest)
            .where(ContactRequest.id == contact_id)
            .values(**values)
        )
        await self.session.execute(stmt)
