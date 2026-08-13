import base64
import html
import json
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Any

import httpx
from fastapi import Request
from hermpers.environment import (
	MAX_REPLY_FILE_UPLOAD_BYTES,
	MAX_REPLY_FILE_UPLOADS,
	MAX_TEXT_ATTACHMENT_CHARS,
	MAX_UPLOAD_BYTES,
)
from starlette.datastructures import UploadFile


logger = logging.getLogger(__name__)

_MENTIONED_FILE_PATTERN = re.compile(
	r"(?:^|[\s\"'(<\[])(?:`)?((?:\./|\.\./|/)[^\s`\"'<>\]\)]+)(?:`)?(?=$|[\s\"'\]>\)])"
)


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


async def parse_request_input(request: Request) -> tuple[str, str, str, list[dict[str, Any]], str]:
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


def _extract_mentioned_file_paths(reply_text: str) -> list[str]:
	if not reply_text:
		return []

	# Replies are HTML-formatted; strip tags to avoid matching closing tags like </pre>.
	normalized = re.sub(r"<[^>]+>", " ", html.unescape(reply_text))
	paths: list[str] = []
	seen: set[str] = set()
	for match in _MENTIONED_FILE_PATTERN.finditer(normalized):
		candidate = (match.group(1) or "").strip()
		if not candidate:
			continue
		if "://" in candidate:
			continue
		if candidate in seen:
			continue
		seen.add(candidate)
		paths.append(candidate)
	return paths


def _resolve_uploadable_files(path_mentions: list[str]) -> list[Path]:
	resolved_files: list[Path] = []
	for mentioned_path in path_mentions:
		candidate = Path(mentioned_path)
		if not candidate.is_absolute():
			candidate = (Path.cwd() / candidate).resolve()
		else:
			candidate = candidate.resolve()

		if not candidate.exists() or not candidate.is_file():
			logger.info("Mentioned file was not found or is not a file: %s", candidate)
			continue

		try:
			size = candidate.stat().st_size
		except OSError:
			logger.info("Unable to stat mentioned file: %s", candidate)
			continue

		if size > MAX_REPLY_FILE_UPLOAD_BYTES:
			logger.info(
				"Mentioned file is too large for upload (%s bytes > %s): %s",
				size,
				MAX_REPLY_FILE_UPLOAD_BYTES,
				candidate,
			)
			continue

		if not os.access(candidate, os.R_OK):
			logger.info("Mentioned file is not readable: %s", candidate)
			continue

		resolved_files.append(candidate)
		if len(resolved_files) >= MAX_REPLY_FILE_UPLOADS:
			logger.info("Reached max reply file uploads limit (%s)", MAX_REPLY_FILE_UPLOADS)
			break

	return resolved_files


def _collect_uploadable_mentioned_files(bot_reply: str) -> list[Path]:
	mentioned_paths = _extract_mentioned_file_paths(bot_reply)
	if not mentioned_paths:
		return []
	return _resolve_uploadable_files(mentioned_paths)


async def _post_file_to_campfire(upload_url: str, file_path: Path) -> bool:
	mime_type, _ = mimetypes.guess_type(str(file_path))
	content_type = mime_type or "application/octet-stream"

	try:
		with file_path.open("rb") as fp:
			async with httpx.AsyncClient(timeout=20.0) as client:
				response = await client.post(
					upload_url,
					files={"attachment": (file_path.name, fp, content_type)},
				)
			response.raise_for_status()
		logger.info("Posted file to Campfire successfully: %s", file_path)
		return True
	except httpx.HTTPStatusError as exc:
		logger.warning(
			"Campfire rejected attachment upload for %s: %s %s",
			file_path,
			exc.response.status_code,
			exc.response.text,
		)
	except OSError:
		logger.warning("Failed to open mentioned file for upload: %s", file_path)
	except httpx.RequestError as exc:
		logger.warning("Request error while uploading mentioned file %s: %s", file_path, str(exc))

	return False


async def post_mentioned_files_to_campfire(target_url: str, bot_reply: str) -> None:
	uploadable_files = _collect_uploadable_mentioned_files(bot_reply)
	if not uploadable_files:
		return

	for file_path in uploadable_files:
		await _post_file_to_campfire(target_url, file_path)