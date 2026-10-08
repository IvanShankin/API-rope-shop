from typing import Type, Union, Any, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import ModelType, DTOType


class BaseRepository:

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    def add(self, data: Union[DTOType, dict]) -> ModelType:
        if isinstance(data, dict):
            instance = self.model(**data)
        elif hasattr(data, "model_dump"):
            instance = self.model(**data.model_dump())
        else:
            instance = self.model(**dict(data))
        self.session.add(instance)
        return instance

    async def get_by_id(self, model: ModelType, obj_id: int) -> ModelType | None:
        stmt = select(model).where(model.id == obj_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()


class BaseIndexedRepository(BaseRepository):
    """
    Базовый репозиторий для моделей с числовым полем порядка `index`.
    Автоматизирует сдвиг индексов при перемещении (reorder), вставке и удалении.
    """

    async def get_max_index(self, **filters: Any) -> int:
        """Получить максимальный индекс среди записей (с учетом фильтров)."""
        stmt = select(func.coalesce(func.max(self.model.index), 0))
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def shift_indexes_for_insert(
        self,
        target_index: int,
        **filters: Any
    ) -> None:
        """
        Сдвигает индексы записей >= target_index на +1 перед вставкой нового элемента.
        """
        stmt = (
            update(self.model)
            .where(self.model.index >= target_index)
            .values(index=self.model.index + 1)
        )
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        await self.session.execute(stmt)

    async def shift_indexes_after_delete(
        self,
        deleted_index: int,
        **filters: Any
    ) -> None:
        """
        Сдвигает индексы записей > deleted_index на -1 после удаления элемента,
        чтобы не оставалось пробелов в последовательности.
        """
        stmt = (
            update(self.model)
            .where(self.model.index > deleted_index)
            .values(index=self.model.index - 1)
        )
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        await self.session.execute(stmt)

    async def reorder_index(
        self,
        obj_id: int,
        old_index: int,
        new_index: int,
        **filters: Any
    ) -> None:
        """
        Перемещает запись с позиции old_index на new_index со сдвигом промежуточных элементов:
        - При new_index < old_index (сдвиг вперед/вверх):
          записи с new_index <= index < old_index сдвигаются на +1.
        - При new_index > old_index (сдвиг назад/вниз):
          записи с old_index < index <= new_index сдвигаются на -1.
        - Перемещаемая запись получает new_index.
        """
        if old_index == new_index:
            return

        if new_index < old_index:
            shift_stmt = (
                update(self.model)
                .where(
                    self.model.index >= new_index,
                    self.model.index < old_index,
                    self.model.id != obj_id,
                )
                .values(index=self.model.index + 1)
            )
        else:
            shift_stmt = (
                update(self.model)
                .where(
                    self.model.index <= new_index,
                    self.model.index > old_index,
                    self.model.id != obj_id,
                )
                .values(index=self.model.index - 1)
            )

        for key, value in filters.items():
            shift_stmt = shift_stmt.where(getattr(self.model, key) == value)

        await self.session.execute(shift_stmt)

        obj_update_stmt = (
            update(self.model)
            .where(self.model.id == obj_id)
            .values(index=new_index)
        )
        await self.session.execute(obj_update_stmt)
