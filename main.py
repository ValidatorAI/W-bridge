import logging
from typing import Any

import uvicorn
import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import PlainTextResponse

from application.logic import generate_and_persist_bot_reply
from application.query import _get_active_bot_by_token_query
from helpers.helpers import str_to_bool
from helpers.upload import parse_request_input, post_mentioned_files_to_campfire
from hermpers.environment import MASTER_KEY_TOKEN, PORT, RELOAD, ROOM_BASE_URL
from db.database import SessionLocal


app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RELOAD = str_to_bool(RELOAD)


def _append_internal_session_footer(message: str, session_key: str | None) -> str:
	session_label = session_key if session_key else "N/A"
	return f'{message}<br/><span class="red">our internal session_key </span>{session_label}'


async def _post_reply(target_url: str, bot_reply: str) -> None:
	try:
		# sanitize bot reply & parapere it for campfire
		bot_reply = bot_reply.replace("%", " percent")
		async with httpx.AsyncClient(timeout=20.0) as client:
			response = await client.post(
				target_url,
				content=bot_reply,
				headers={"Content-Type": "text/html; charset=utf-8"},
			)
			response.raise_for_status()
		logger.info("Posted reply to Campfire successfully!")
	except httpx.HTTPStatusError as exc:
		logger.error(
			"Post Error: %s %s | url=%s",
			exc.response.status_code,
			exc.response.text,
			str(exc.request.url),
		)
	except httpx.RequestError as exc:
		logger.error("Request Error: %s", str(exc))


async def _process_webhook(
	user_name: str,
	room_path: str,
	raw_content: str,
	attachment_parts: list[dict[str, Any]],
	attachment_log: str,
	profile_name: str,
) -> None:
	if not raw_content and not attachment_parts:
		logger.warning(
			"Empty message and no attachments. Skipping. user=%s room=%s",
			user_name,
			room_path or "N/A",
		)
		return

	if raw_content:
		logger.info('[Raw HTML Received]: "%s"', raw_content)
	if attachment_log:
		logger.info("Attachments received: %s", attachment_log)

	if not room_path:
		logger.error("Room path missing in payload/form data")
		return

	target_url = f"{ROOM_BASE_URL}{room_path}"

	bot_reply, local_session_key = await generate_and_persist_bot_reply(
		user_name,
		room_path,
		raw_content,
		attachment_parts=attachment_parts,
		attachment_log=attachment_log,
		profile_name=profile_name,
	)

	logger.info("Sending reply to: %s", target_url)
	if bot_reply == "Help":
		help_message = (
			"Available commands:<br/>"
			"<a>/new</a>: Start a new session.<br/>"
			"<a>/single</a>: Use single message mode.<br/>"
			"<a>/session:name</a>: Use a named session.<br/>"
			"<a>/fork:name</a>: Fork the active session into a new named branch.<br/>"
			"<a>/h</a> or <a>/help</a>: Show this help message."
		)
		await _post_reply(target_url, _append_internal_session_footer(help_message, local_session_key))
	#else:
		#rendered_reply = _append_internal_session_footer(bot_reply, local_session_key)
		#await _post_reply(target_url, rendered_reply)
		# await post_mentioned_files_to_campfire(target_url, bot_reply)

	


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks) -> PlainTextResponse:
	token = str(request.query_params.get("token") or "").strip()
	if not token:
		return PlainTextResponse("credential is not exists or known", status_code=200)

	selected_profile = "default"
	if MASTER_KEY_TOKEN and token == MASTER_KEY_TOKEN:
		selected_profile = "default"
	else:
		with SessionLocal() as db:
			bot = _get_active_bot_by_token_query(db, token)
		if bot is None:
			return PlainTextResponse("credential is not exists or known", status_code=200)
		selected_profile = (bot.profile_name or "default").strip() or "default"

	user_name, room_path, raw_content, attachment_parts, attachment_log = await parse_request_input(request)

	background_tasks.add_task(
		_process_webhook,
		user_name,
		room_path,
		raw_content,
		attachment_parts,
		attachment_log,
		selected_profile,
	)

	return PlainTextResponse("", status_code=200)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT), reload=RELOAD)