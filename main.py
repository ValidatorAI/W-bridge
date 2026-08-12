import html
import logging
import re
from typing import Any
import os
import asyncio
import base64
import json
import uvicorn
import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import PlainTextResponse
from starlette.datastructures import UploadFile
from sqlalchemy.orm import Session

from application.logic import generate_and_persist_bot_reply
from helpers.helpers import str_to_bool
from db.database import SessionLocal
from db.models import MessageLog


app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOM_BASE_URL = os.getenv("ROOM_BASE_URL", "https://chat.nvgtrs.io").rstrip("/")
PORT = os.getenv("PORT", "80")
RELOAD = str_to_bool(os.getenv("RELOAD", "False"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
MAX_TEXT_ATTACHMENT_CHARS = int(os.getenv("MAX_TEXT_ATTACHMENT_CHARS", "12000"))


def _is_textual_content_type(content_type: str | None) -> bool:
	if not content_type:
		return False
	content_type = content_type.lower()
	if content_type.startswith("text/"):
		return True
	return content_type in {
		"application/json",
		"application/xml",
		"application/x-yaml",
		"application/yaml",
	}


def _extract_url_from_attachment(item: dict[str, Any]) -> str | None:
	for key in ("url", "download_url", "href", "src", "image_url"):
		value = item.get(key)
		if isinstance(value, str) and value.strip():
			return value.strip()
	return None


def _extract_raw_text_from_message_payload(message_payload: dict[str, Any]) -> str:
	body = message_payload.get("body")
	if isinstance(body, dict):
		for key in ("html", "text", "plain", "raw", "markdown"):
			value = body.get(key)
			if isinstance(value, str) and value.strip():
				return value.strip()

	for key in ("html", "text", "plain", "raw", "markdown"):
		value = message_payload.get(key)
		if isinstance(value, str) and value.strip():
			return value.strip()

	return ""


def _iter_attachment_candidates(message_payload: dict[str, Any]) -> list[dict[str, Any]]:
	candidates: list[dict[str, Any]] = []
	body = message_payload.get("body")

	search_spaces: list[dict[str, Any]] = [message_payload]
	if isinstance(body, dict):
		search_spaces.append(body)

	for space in search_spaces:
		for key in ("attachments", "files", "uploads", "file", "upload"):
			value = space.get(key)
			if isinstance(value, dict):
				candidates.append(value)
			elif isinstance(value, list):
				for item in value:
					if isinstance(item, dict):
						candidates.append(item)

	return candidates


def _parse_payload_field_from_form(raw_payload: str | None) -> dict[str, Any] | None:
	if not raw_payload or not raw_payload.strip():
		return None
	try:
		parsed = json.loads(raw_payload)
		if isinstance(parsed, dict):
			return parsed
	except json.JSONDecodeError:
		logger.warning("Form payload field is not valid JSON")
	return None


def _build_text_part_from_multipart_file(
	filename: str,
	content_type: str,
	data: bytes,
) -> dict[str, str]:
	decoded = data.decode("utf-8", errors="replace")
	truncated = decoded[:MAX_TEXT_ATTACHMENT_CHARS]
	suffix = ""
	if len(decoded) > len(truncated):
		suffix = "\n\n[File content truncated for size limits.]"
	return {
		"type": "text",
		"text": f"Attached file '{filename}' ({content_type}):\n\n{truncated}{suffix}",
	}


def _build_non_image_notice_part(filename: str, content_type: str, size: int) -> dict[str, str]:
	return {
		"type": "text",
		"text": (
			f"Attached file '{filename}' ({content_type}, {size} bytes). "
			"Direct binary file upload is not supported by Hermes API in this bridge; "
			"include relevant file text in your message when needed."
		),
	}


async def _parse_request_input(request: Request) -> tuple[str, str, str, list[dict[str, Any]], str]:
	content_type = (request.headers.get("content-type") or "").lower()
	attachment_parts: list[dict[str, Any]] = []
	attachment_log_entries: list[str] = []

	if "multipart/form-data" in content_type:
		form = await request.form()

		parsed_payload = _parse_payload_field_from_form(str(form.get("payload") or "").strip() or None)
		message_payload_from_form = parsed_payload.get("message") if isinstance(parsed_payload, dict) and isinstance(parsed_payload.get("message"), dict) else {}

		room_path = str(
			form.get("room_path")
			or form.get("room")
			or ((parsed_payload or {}).get("room") or {}).get("path")
			or ""
		).strip()
		user_name = str(
			form.get("user_name")
			or form.get("user")
			or ((parsed_payload or {}).get("user") or {}).get("name")
			or "User"
		).strip() or "User"
		raw_content = str(form.get("message") or form.get("text") or form.get("raw_content") or "").strip()
		if not raw_content and message_payload_from_form:
			raw_content = _extract_raw_text_from_message_payload(message_payload_from_form)

		for key, value in form.multi_items():
			if not isinstance(value, UploadFile):
				continue

			filename = (getattr(value, "filename", None) or "uploaded-file").strip() or "uploaded-file"
			file_content_type = (getattr(value, "content_type", None) or "application/octet-stream").strip()
			data = await value.read()
			size = len(data)

			if size == 0:
				logger.info("Skipping empty uploaded file: %s", filename)
				continue

			if size > MAX_UPLOAD_BYTES:
				attachment_parts.append(
					{
						"type": "text",
						"text": (
							f"Attached file '{filename}' is too large ({size} bytes). "
							f"Current bridge limit is {MAX_UPLOAD_BYTES} bytes."
						),
					}
				)
				attachment_log_entries.append(f"{filename} ({file_content_type}, {size} bytes, too large)")
				continue

			if file_content_type.startswith("image/"):
				data_b64 = base64.b64encode(data).decode("ascii")
				data_url = f"data:{file_content_type};base64,{data_b64}"
				attachment_parts.append(
					{
						"type": "image_url",
						"image_url": {
							"url": data_url,
							"detail": "auto",
						},
					}
				)
			elif _is_textual_content_type(file_content_type):
				attachment_parts.append(_build_text_part_from_multipart_file(filename, file_content_type, data))
			else:
				attachment_parts.append(_build_non_image_notice_part(filename, file_content_type, size))

			attachment_log_entries.append(f"{filename} ({file_content_type}, {size} bytes)")
			logger.info("Accepted uploaded file from form key '%s': %s", key, attachment_log_entries[-1])

		attachment_log = ", ".join(attachment_log_entries)
		return (user_name, room_path, raw_content, attachment_parts, attachment_log)

	payload = await request.json()
	message_payload = payload.get("message") if isinstance(payload.get("message"), dict) else {}
	raw_content = _extract_raw_text_from_message_payload(message_payload)

	room_path = str((payload.get("room") or {}).get("path") or "").strip()
	user_name = str((payload.get("user") or {}).get("name") or "User").strip() or "User"

	for item in _iter_attachment_candidates(message_payload):
		url = _extract_url_from_attachment(item)
		if not url:
			continue

		filename = str(item.get("name") or item.get("filename") or "uploaded-file").strip() or "uploaded-file"
		mime = str(item.get("content_type") or item.get("mime_type") or "").strip().lower()

		if url.startswith("data:image/") or mime.startswith("image/"):
			attachment_parts.append(
				{
					"type": "image_url",
					"image_url": {
						"url": url,
						"detail": "auto",
					},
				}
			)
		else:
			attachment_parts.append(
				{
					"type": "text",
					"text": f"Attached file '{filename}': {url}",
				}
			)

		attachment_log_entries.append(f"{filename} ({mime or 'unknown'})")

	attachment_log = ", ".join(attachment_log_entries)
	return (user_name, room_path, raw_content, attachment_parts, attachment_log)


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
	else:
		await _post_reply(target_url, _append_internal_session_footer(bot_reply, local_session_key))

	


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks) -> PlainTextResponse:
	user_name, room_path, raw_content, attachment_parts, attachment_log = await _parse_request_input(request)
	background_tasks.add_task(
		_process_webhook,
		user_name,
		room_path,
		raw_content,
		attachment_parts,
		attachment_log,
	)
	return PlainTextResponse("OK", status_code=200)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT), reload=RELOAD)