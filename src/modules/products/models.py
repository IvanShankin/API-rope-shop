from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database.database import Base

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
