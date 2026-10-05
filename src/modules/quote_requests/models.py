from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, func, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from src.core.database.database import Base


class QuoteRequest(Base):
    __tablename__ = "quote_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    configurator_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    configuration_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_splices: Mapped[int] = mapped_column(Integer, nullable=False)
    
    rope_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    splice_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    extras_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    urgent_surcharge: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    
    is_urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="new")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

