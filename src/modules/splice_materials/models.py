from typing import TYPE_CHECKING, List
from sqlalchemy import String, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database.database import Base


if TYPE_CHECKING:
    from src.modules.splice_prices.models import SplicePriceRule


class SpliceMaterial(Base):
    __tablename__ = "splice_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    rules: Mapped[List["SplicePriceRule"]] = relationship("SplicePriceRule", back_populates="splice_material", cascade="all, delete-orphan")

