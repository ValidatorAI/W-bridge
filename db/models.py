from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
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


class BotReply(Base):
    __tablename__ = "bot_replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message_logs.id"), nullable=False, index=True)
    reply_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message: Mapped[MessageLog] = relationship(back_populates="bot_replies")


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_key: Mapped[str] = mapped_column(Text, nullable=False)
    room_id: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    room_pointers: Mapped[list["RoomPointer"]] = relationship(back_populates="session")


class RoomPointer(Base):
    __tablename__ = "room_pointers"

    room_id: Mapped[str] = mapped_column(Text, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id"), nullable=False, index=True)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped[Session] = relationship(back_populates="room_pointers")
