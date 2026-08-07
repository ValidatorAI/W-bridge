import asyncio
import logging

from ai import send_chat
from application.command import _save_bot_reply_sync, _save_message_log_sync


logger = logging.getLogger(__name__)


async def generate_and_persist_bot_reply(
	user_name: str,
	room_path: str,
	raw_content: str,
	cleaned_text: str,
) -> str:
	message_id = await asyncio.to_thread(
		_save_message_log_sync,
		user_name,
		room_path,
		raw_content,
	)

	bot_reply = await send_chat(cleaned_text)

	if message_id is not None:
		await asyncio.to_thread(_save_bot_reply_sync, message_id, bot_reply)
	else:
		logger.warning("Skipping bot reply persistence because message log id is unavailable")

	return bot_reply
