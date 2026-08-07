import asyncio
import logging
import re
import uuid
from ai import send_chat_history
from application.command import _create_message_session_sync, _create_reply_session_sync, _create_session_sync, _get_active_session_id_by_room_sync, _get_session_history_sync, _get_session_id_by_key_and_room_sync, _save_bot_reply_sync, _save_message_log_sync


logger = logging.getLogger(__name__)

# user commands 
# /new -> new session
# /single -> without any session
# /session:session-name -> answer based on session name 
# no command in the text -> normal handler


def _strip_command_occurrence(raw_content: str, command: str) -> str:
	stripped = raw_content.replace(command, "", 1).strip()
	return stripped or raw_content.strip()


def prepare_new_message(
	message_id,
	user_name,
	room_path,
	raw_content,
) -> list:
	match = re.search(r"/new(?::([^\s]+))?", raw_content)
	if match is None:
		session_name = f"session-{uuid.uuid4().hex[:4]}"
		content = raw_content.strip()
	else:
		session_name = (match.group(1) or "").strip() or f"session-{uuid.uuid4().hex[:4]}"
		content = (raw_content[:match.start()] + raw_content[match.end():]).strip() or raw_content.strip()

	session_id = _create_session_sync(session_name, room_path)
	if message_id is not None and session_id is not None:
		_create_message_session_sync(message_id, session_id)
    
	return [
		{
			"role": "system",
			"content": (
				f"message_id={message_id}; user={user_name}; room={room_path}. "
				f"Start a fresh session named '{session_name}' and ignore earlier context."
			),
		},
		{"role": "user", "content": content},
	]


def prepare_single_message(
	message_id,
	user_name,
	room_path,
	raw_content,
) -> list:
    content = _strip_command_occurrence(raw_content, "/single")

    return [
        {"role": "user", "content": content},
    ]


def prepare_named_session_message(
	message_id,
	user_name,
	room_path,
	raw_content,
) -> list:
	match = re.search(r"/session:([^\s]+)", raw_content)
	if match is None:
		return prepare_normal_message(message_id, user_name, room_path, raw_content)

	session_name = match.group(1).strip()
	content = (raw_content[:match.start()] + raw_content[match.end():]).strip() or raw_content.strip()

	session_id = _get_session_id_by_key_and_room_sync(session_name, room_path)
	if message_id is not None and session_id is not None:
		_create_message_session_sync(message_id, session_id)

	session_history = _get_session_history_sync(session_id) if session_id is not None else []

	return [
		{
			"role": "system",
			"content": (
				f"message_id={message_id}; user={user_name}; room={room_path}. "
				f"Use session named '{session_name}' as context key."
			),
		},
		*session_history,
		{"role": "user", "content": content},
	]


def prepare_normal_message(
	message_id,
	user_name,
	room_path,
	raw_content,
) -> list:
	session_id = _get_active_session_id_by_room_sync(room_path)
	if session_id is None:
		session_key = f"session-{uuid.uuid4().hex[:4]}"
		session_id = _create_session_sync(session_key, room_path)

	if message_id is not None and session_id is not None:
		_create_message_session_sync(message_id, session_id)

	session_history = _get_session_history_sync(session_id) if session_id is not None else []

	return [
		*session_history,
		{"role": "user", "content": raw_content.strip()},
	]


def prepare_base_message(
    message_id,
    user_name,
	room_path,
	raw_content,
) -> list:
	normalized = raw_content.strip()

	if "/new" in normalized:
		return prepare_new_message(message_id, user_name, room_path, raw_content)
	if "/single" in normalized:
		return prepare_single_message(message_id, user_name, room_path, raw_content)
	if "/session:" in normalized:
		return prepare_named_session_message(message_id, user_name, room_path, raw_content)
	return prepare_normal_message(message_id, user_name, room_path, raw_content)

async def generate_and_persist_bot_reply(
	user_name: str,
	room_path: str,
	raw_content: str,
) -> str:
	message_id = await asyncio.to_thread(
		_save_message_log_sync,
		user_name,
		room_path,
		raw_content,
	)

	message_payload = prepare_base_message(
		message_id,
		user_name,
		room_path,
		raw_content,
	)
	
	bot_reply = await send_chat_history(message_payload)

	if message_id is not None:
		bot_reply_id = await asyncio.to_thread(_save_bot_reply_sync, message_id, bot_reply)
		if bot_reply_id is not None:
			await asyncio.to_thread(_create_reply_session_sync, bot_reply_id, room_path)
		else:
			logger.warning("Skipping reply-session persistence because bot reply id is unavailable")
	else:
		logger.warning("Skipping bot reply persistence because message log id is unavailable")

	return bot_reply