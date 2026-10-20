from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.base.database_model import (
    BaseModelWithRelationshipTranslation,
    BaseTranslation,
)


class ContentBlock(BaseModelWithRelationshipTranslation):
    __tablename__ = "content_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    block_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
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

    __table_args__ = (
        UniqueConstraint("page_code", "block_code", name="uq_content_block_page_code"),
    )

    translations: Mapped[List["ContentBlockTranslation"]] = relationship(
        "ContentBlockTranslation",
        back_populates="content_block",
        cascade="all, delete-orphan",
        order_by="ContentBlockTranslation.id",
    )


class ContentBlockTranslation(BaseTranslation):
    __tablename__ = "content_block_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("content_blocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    content_block: Mapped["ContentBlock"] = relationship(
        "ContentBlock",
        back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint(
            "content_block_id", "locale", name="uq_content_block_id_locale"
        ),
    )
