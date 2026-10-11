from typing import Optional, Sequence, Union, Any
from datetime import datetime

from sqlalchemy import select, update, delete, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository
from src.modules.quote_requests.models import (
    QuoteRequest,
    QuoteRopeItem,
    QuoteServiceItem,
    QuoteExtraItem,
    QuoteRequestStatus,
    ConfiguratorType,
)
from src.modules.quote_requests.models_dto import (
    QuoteRequestInsertDTO,
    QuoteRopeItemInsertDTO,
    QuoteServiceItemInsertDTO,
    QuoteExtraItemInsertDTO,
)


class QuoteRequestRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=QuoteRequest)

    async def add_quote_request(self, data: Union[QuoteRequestInsertDTO, dict, Any]) -> QuoteRequest:
        """Добавление новой заявки."""
        return self.add(data)

    async def get_by_id(
        self,
        request_id: int,
        include_relations: bool = True,
    ) -> QuoteRequest | None:
        """Получение заявки по ID с предзагрузкой всех позиций."""
        stmt = select(QuoteRequest).where(QuoteRequest.id == request_id)
        if include_relations:
            stmt = stmt.options(
                selectinload(QuoteRequest.rope_items),
                selectinload(QuoteRequest.service_items),
                selectinload(QuoteRequest.extra_items),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_request_number(
        self,
        request_number: str,
        include_relations: bool = True,
    ) -> QuoteRequest | None:
        """Получение заявки по номеру заявки."""
        stmt = select(QuoteRequest).where(QuoteRequest.request_number == request_number)
        if include_relations:
            stmt = stmt.options(
                selectinload(QuoteRequest.rope_items),
                selectinload(QuoteRequest.service_items),
                selectinload(QuoteRequest.extra_items),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_requests_by_year(self, year: int) -> int:
        """Подсчет количества заявок с префиксом текущего года (для генератора номера)."""
        prefix = f"RPL-{year}-%"
        stmt = select(func.count(QuoteRequest.id)).where(QuoteRequest.request_number.like(prefix))
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def get_all(
        self,
        status: Optional[QuoteRequestStatus] = None,
        configurator_type: Optional[ConfiguratorType] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        request_number: Optional[str] = None,
        is_urgent: Optional[bool] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[QuoteRequest]:
        """Получение списка заявок с расширенной фильтрацией, сортировкой и пагинацией."""
        stmt = select(QuoteRequest).options(
            selectinload(QuoteRequest.rope_items),
            selectinload(QuoteRequest.service_items),
            selectinload(QuoteRequest.extra_items),
        )

        # Фильтры
        if status is not None:
            stmt = stmt.where(QuoteRequest.status == status)
        if configurator_type is not None:
            stmt = stmt.where(QuoteRequest.configurator_type == configurator_type)
        if name:
            stmt = stmt.where(QuoteRequest.name.ilike(f"%{name}%"))
        if email:
            stmt = stmt.where(QuoteRequest.email.ilike(f"%{email}%"))
        if phone:
            stmt = stmt.where(QuoteRequest.phone.ilike(f"%{phone}%"))
        if request_number:
            stmt = stmt.where(QuoteRequest.request_number.ilike(f"%{request_number}%"))
        if is_urgent is not None:
            stmt = stmt.where(QuoteRequest.is_urgent == is_urgent)
        if created_from is not None:
            stmt = stmt.where(QuoteRequest.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(QuoteRequest.created_at <= created_to)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    QuoteRequest.request_number.ilike(search_pattern),
                    QuoteRequest.name.ilike(search_pattern),
                    QuoteRequest.email.ilike(search_pattern),
                    QuoteRequest.phone.ilike(search_pattern),
                )
            )

        # Сортировка
        sort_column = getattr(QuoteRequest, sort_by, QuoteRequest.created_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(asc(sort_column))
        else:
            stmt = stmt.order_by(desc(sort_column))

        # Пагинация
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_quote_request(self, request_id: int, update_data: dict) -> None:
        """Обновление данных заявки."""
        stmt = update(QuoteRequest).where(QuoteRequest.id == request_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_quote_request(self, request_id: int) -> None:
        """Удаление заявки (позиции удаляются каскадно)."""
        stmt = delete(QuoteRequest).where(QuoteRequest.id == request_id)
        await self.session.execute(stmt)

    async def has_dependencies(self, request_id: int) -> bool:
        """Проверка наличия внешних зависимостей (Правило 5.1)."""
        return False


class QuoteRopeItemRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=QuoteRopeItem)

    async def add_item(self, data: Union[QuoteRopeItemInsertDTO, dict, Any]) -> QuoteRopeItem:
        """Добавление позиции каната."""
        return self.add(data)

    async def get_by_id(self, item_id: int) -> QuoteRopeItem | None:
        """Получение позиции каната по ID."""
        stmt = select(QuoteRopeItem).where(QuoteRopeItem.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_item(self, item_id: int) -> None:
        """Удаление позиции каната."""
        stmt = delete(QuoteRopeItem).where(QuoteRopeItem.id == item_id)
        await self.session.execute(stmt)


class QuoteServiceItemRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=QuoteServiceItem)

    async def add_item(self, data: Union[QuoteServiceItemInsertDTO, dict, Any]) -> QuoteServiceItem:
        """Добавление позиции услуги."""
        return self.add(data)

    async def get_by_id(self, item_id: int) -> QuoteServiceItem | None:
        """Получение позиции услуги по ID."""
        stmt = select(QuoteServiceItem).where(QuoteServiceItem.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_item(self, item_id: int) -> None:
        """Удаление позиции услуги."""
        stmt = delete(QuoteServiceItem).where(QuoteServiceItem.id == item_id)
        await self.session.execute(stmt)


class QuoteExtraItemRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=QuoteExtraItem)

    async def add_item(self, data: Union[QuoteExtraItemInsertDTO, dict, Any]) -> QuoteExtraItem:
        """Добавление позиции доп. опции."""
        return self.add(data)

    async def get_by_id(self, item_id: int) -> QuoteExtraItem | None:
        """Получение позиции доп. опции по ID."""
        stmt = select(QuoteExtraItem).where(QuoteExtraItem.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_item(self, item_id: int) -> None:
        """Удаление позиции доп. опции."""
        stmt = delete(QuoteExtraItem).where(QuoteExtraItem.id == item_id)
        await self.session.execute(stmt)
