from sqlalchemy.orm import Session

from db.models import Bot


def _get_active_bot_by_token_query(db: Session, token: str) -> Bot | None:
	return db.query(Bot).filter(Bot.token == token, Bot.active.is_(True)).first()
