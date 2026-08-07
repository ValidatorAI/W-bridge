from typing import cast

from sqlalchemy.orm import Session

from db.models import BotReply, MessageLog, MessageSession, RoomPointer, Session as ChatSession


def _get_room_pointer_by_room_id_query(db: Session, room_id: str) -> RoomPointer | None:
	return db.query(RoomPointer).filter(RoomPointer.room_id == room_id).first()


def _get_session_by_key_and_room_query(db: Session, session_key: str, room_id: str) -> ChatSession | None:
	return (
		db.query(ChatSession)
		.filter(ChatSession.session_key == session_key, ChatSession.room_id == room_id)
		.order_by(ChatSession.session_id.desc())
		.first()
	)


def _get_session_by_id_query(db: Session, session_id: int) -> ChatSession | None:
	return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()


def _get_session_message_reply_rows_query(db: Session, session_id: int) -> list[tuple[MessageLog, BotReply | None]]:
	return cast(
		list[tuple[MessageLog, BotReply | None]],
		(
		db.query(MessageLog, BotReply)
		.join(MessageSession, MessageSession.message_id == MessageLog.id)
		.outerjoin(BotReply, BotReply.message_id == MessageLog.id)
		.filter(MessageSession.session_id == session_id)
		.order_by(MessageLog.created_at.asc(), BotReply.created_at.asc())
		.all()
		),
	)
