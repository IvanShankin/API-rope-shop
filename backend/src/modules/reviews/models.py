import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import Base
from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
    Language,
)


class ReviewsStatus(str, enum.Enum):
    NEW = "new"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"


# Alias for convenience
ReviewStatus = ReviewsStatus


class Review(BaseModelWithRelationshipTranslation):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    status: Mapped[ReviewsStatus] = mapped_column(
        Enum(
            ReviewsStatus,
            values_callable=lambda x: [e.value for e in x],
            name="review_status",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=ReviewsStatus.NEW,
        server_default=ReviewsStatus.NEW.value,
    )
    index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    translations: Mapped[List["ReviewTranslation"]] = relationship(
        "ReviewTranslation",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="ReviewTranslation.id",
    )


class ReviewTranslation(BaseTranslation):
    __tablename__ = "review_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)

    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint("review_id", "locale", name="uq_review_id_locale"),
    )
