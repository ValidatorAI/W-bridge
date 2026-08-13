from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class MessageLog(Base):
    __tablename__ = "message_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_path: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_html: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    bot_replies: Mapped[list["BotReply"]] = relationship(back_populates="message")
    message_sessions: Mapped[list["MessageSession"]] = relationship(back_populates="message")


class BotReply(Base):
    __tablename__ = "bot_replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message_logs.id"), nullable=False, index=True)
    reply_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message: Mapped[MessageLog] = relationship(back_populates="bot_replies")
    reply_sessions: Mapped[list["ReplySession"]] = relationship(back_populates="reply")


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_name: Mapped[str] = mapped_column(String(255), nullable=False, default="default", server_default="default")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_key: Mapped[str] = mapped_column(Text, nullable=False)
    room_id: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    room_pointers: Mapped[list["RoomPointer"]] = relationship(back_populates="session")
    message_sessions: Mapped[list["MessageSession"]] = relationship(back_populates="session")
    reply_sessions: Mapped[list["ReplySession"]] = relationship(back_populates="session")
    hermes_sessions: Mapped[list["HermesSession"]] = relationship(back_populates="session")


class RoomPointer(Base):
    __tablename__ = "room_pointers"

    room_id: Mapped[str] = mapped_column(Text, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id"), nullable=False, index=True)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped[Session] = relationship(back_populates="room_pointers")


class MessageSession(Base):
    __tablename__ = "message_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message_logs.id"), nullable=False, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id"), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message: Mapped[MessageLog] = relationship(back_populates="message_sessions")
    session: Mapped[Session] = relationship(back_populates="message_sessions")


class ReplySession(Base):
    __tablename__ = "reply_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reply_id: Mapped[int] = mapped_column(ForeignKey("bot_replies.id"), nullable=False, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id"), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reply: Mapped[BotReply] = relationship(back_populates="reply_sessions")
    session: Mapped[Session] = relationship(back_populates="reply_sessions")


class HermesSession(Base):
    __tablename__ = "hermes_sessions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    is_forked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    parent: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id"), nullable=False, index=True)

    session: Mapped[Session] = relationship(back_populates="hermes_sessions")


class HermessMessage(Base):
    __tablename__ = "hermess_messages"

    hermes_message_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_bot_reply: Mapped[bool] = mapped_column(Boolean, nullable=False)
