from datetime import datetime
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
    stored_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)


class McpException(Base):
    __tablename__ = "mcp_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_call_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exception: Mapped[str] = mapped_column(Text, nullable=False)
    stored_exception: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ApiException(Base):
    __tablename__ = "api_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    endpoint: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_type: Mapped[str] = mapped_column(String(255), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stored_exception: Mapped[str] = mapped_column(Text, nullable=False)
    request_context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class McpCallLog(Base):
    __tablename__ = "mcp_call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    jsonrpc_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_call_name: Mapped[str] = mapped_column(String(255), nullable=False)
    params_sanitized: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_error: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


