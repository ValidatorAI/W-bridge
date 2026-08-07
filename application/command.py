from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import BotReply, MessageLog, MessageSession, ReplySession, RoomPointer, Session as ChatSession
from application.query import _get_room_pointer_by_room_id_query, _get_session_by_id_query, _get_session_by_key_and_room_query, _get_session_message_reply_rows_query
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def _save_message_log_sync(
	user_name: str,
	room_path: str,
	raw_html: str,
) -> int | None:
	db: Session = SessionLocal()
	try:
		log_item = MessageLog(
			user_name=user_name,
			room_path=room_path,
			raw_html=raw_html,
		)
		db.add(log_item)
		db.commit()
		db.refresh(log_item)
		return log_item.id
	except Exception:
		db.rollback()
		logger.exception("Failed to save message log")
		return None
	finally:
		db.close()


def _save_bot_reply_sync(message_id: int, reply_text: str) -> int | None:
	db: Session = SessionLocal()
	try:
		reply_item = BotReply(
			message_id=message_id,
			reply_text=reply_text,
		)
		db.add(reply_item)
		db.commit()
		db.refresh(reply_item)
		return reply_item.id
	except Exception:
		db.rollback()
		logger.exception("Failed to save bot reply")
		return None
	finally:
		db.close()


def _create_session_sync(session_key: str, room_id: str) -> int | None:
	db: Session = SessionLocal()
	try:
		updated_at = datetime.now(timezone.utc).isoformat()
		session_item = ChatSession(
			session_key=session_key,
			room_id=room_id,
			updated_at=updated_at,
		)
		db.add(session_item)
		db.flush()
		existing_pointer = _get_room_pointer_by_room_id_query(db, room_id)
		if existing_pointer is None:
			db.add(
				RoomPointer(
					room_id=room_id,
					session_id=session_item.session_id,
					updated_at=updated_at,
				)
			)
		else:
			existing_pointer.session_id = session_item.session_id
			existing_pointer.updated_at = updated_at
		db.commit()
		db.refresh(session_item)
		return session_item.session_id
	except Exception:
		db.rollback()
		logger.exception("Failed to create session")
		return None
	finally:
		db.close()


def _create_message_session_sync(message_id: int, session_id: int) -> None:
	db: Session = SessionLocal()
	try:
		message_session_item = MessageSession(
			message_id=message_id,
			session_id=session_id,
		)
		db.add(message_session_item)
		db.commit()
	except Exception:
		db.rollback()
		logger.exception("Failed to create message session link")
	finally:
		db.close()


def _create_reply_session_sync(reply_id: int, room_id: str) -> None:
	db: Session = SessionLocal()
	try:
		existing_pointer = _get_room_pointer_by_room_id_query(db, room_id)
		if existing_pointer is None:
			logger.warning("Skipping reply-session link because no room pointer exists")
			return

		reply_session_item = ReplySession(
			reply_id=reply_id,
			session_id=existing_pointer.session_id,
		)
		db.add(reply_session_item)
		db.commit()
	except Exception:
		db.rollback()
		logger.exception("Failed to create reply session link")
	finally:
		db.close()


def _get_session_id_by_key_and_room_sync(session_key: str, room_id: str) -> int | None:
	db: Session = SessionLocal()
	try:
		session_item = _get_session_by_key_and_room_query(db, session_key, room_id)
		if session_item is None:
			return None
		return session_item.session_id
	except Exception:
		logger.exception("Failed to fetch session id by key and room")
		return None
	finally:
		db.close()


def _get_active_session_id_by_room_sync(room_id: str) -> int | None:
	db: Session = SessionLocal()
	try:
		existing_pointer = _get_room_pointer_by_room_id_query(db, room_id)
		if existing_pointer is None:
			return None

		session_item = _get_session_by_id_query(db, existing_pointer.session_id)
		if session_item is None:
			return None

		return session_item.session_id
	except Exception:
		logger.exception("Failed to fetch active session id by room")
		return None
	finally:
		db.close()


def _get_session_history_sync(session_id: int) -> list[dict[str, str]]:
	db: Session = SessionLocal()
	try:
		rows = _get_session_message_reply_rows_query(db, session_id)
		history: list[dict[str, str]] = []
		for message_log, bot_reply in rows:
			history.append({"role": "user", "content": message_log.raw_html})
			if bot_reply is not None:
				history.append({"role": "assistant", "content": bot_reply.reply_text})
		return history
	except Exception:
		logger.exception("Failed to fetch session history")
		return []
	finally:
		db.close()