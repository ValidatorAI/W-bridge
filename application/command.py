from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import BotReply, MessageLog
import logging

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


def _save_bot_reply_sync(message_id: int, reply_text: str) -> None:
	db: Session = SessionLocal()
	try:
		reply_item = BotReply(
			message_id=message_id,
			reply_text=reply_text,
		)
		db.add(reply_item)
		db.commit()
	except Exception:
		db.rollback()
		logger.exception("Failed to save bot reply")
	finally:
		db.close()