from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database.database import Base

if TYPE_CHECKING:
    from src.modules.categories.models import Category


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )

    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="products",
    )
