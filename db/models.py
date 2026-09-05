from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_name: Mapped[str] = mapped_column(String(255), nullable=False, default="default", server_default="default")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class SpaceEvent(Base):
    __tablename__ = "space_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    space_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    group_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stored_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)


class McpException(Base):
    __tablename__ = "mcp_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_call_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exception: Mapped[str] = mapped_column(Text, nullable=False)
    stored_exception: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


