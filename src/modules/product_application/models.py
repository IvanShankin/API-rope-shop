from typing import List, TYPE_CHECKING
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base
from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
)

if TYPE_CHECKING:
    from src.modules.products.models import Product



class ProductApplication(BaseModelWithRelationshipTranslation):
    __tablename__ = "product_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    translations: Mapped[List["ProductApplicationTranslation"]] = relationship(
        "ProductApplicationTranslation",
        back_populates="application",
        cascade="all, delete-orphan",
    )
    assigned_products: Mapped[List["ProductAssignedApplication"]] = relationship(
        "ProductAssignedApplication",
        back_populates="application",
        cascade="all, delete-orphan",
    )


class ProductApplicationTranslation(BaseTranslation):
    __tablename__ = "product_application_translations"
    __table_args__ = (
        UniqueConstraint("application_id", "locale", name="uq_product_app_trans_app_locale"),
    )

    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    application: Mapped["ProductApplication"] = relationship(
        "ProductApplication", back_populates="translations"
    )


class ProductAssignedApplication(Base):
    __tablename__ = "product_assigned_applications"
    __table_args__ = (
        UniqueConstraint("product_id", "application_id", name="uq_product_assigned_app"),
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_applications.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product: Mapped["Product"] = relationship("Product", back_populates="assigned_applications")
    application: Mapped["ProductApplication"] = relationship("ProductApplication", back_populates="assigned_products")
