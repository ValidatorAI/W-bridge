import html
import logging
import re
from typing import Any
import os
import asyncio
import uvicorn
import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from application.logic import generate_and_persist_bot_reply
from helpers import str_to_bool
from db.database import SessionLocal
from db.models import MessageLog


app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOM_BASE_URL = os.getenv("ROOM_BASE_URL", "https://chat.nvgtrs.io").rstrip("/")
PORT = os.getenv("PORT", "80")
RELOAD = str_to_bool(os.getenv("RELOAD", "False"))


async def _post_reply(target_url: str, bot_reply: str) -> None:
	try:
		async with httpx.AsyncClient(timeout=20.0) as client:
			await client.post(
				target_url,
				json=bot_reply,
				headers={"Content-Type": "application/json"},
			)
		logger.info("Posted reply to Campfire successfully!")
	except httpx.HTTPError as exc:
		response = getattr(exc, "response", None)
		if response is not None:
			logger.error("Post Error: %s %s", response.status_code, response.text)
		else:
			logger.error("Post Error: %s", str(exc))




async def _process_webhook(payload: dict[str, Any]) -> None:
	raw_content = (payload.get("message") or {}).get("body", {}).get("html") or ""

	if not isinstance(raw_content, str) or not raw_content.strip():
		logger.warning("Empty message or missing html body. Skipping.")
		return

	logger.info('[Raw HTML Received]: "%s"', raw_content)

	room_path = (payload.get("room") or {}).get("path")
	if not room_path:
		logger.error("Room path missing in payload")
		return

	target_url = f"{ROOM_BASE_URL}{room_path}"

	user_name = (payload.get("user") or {}).get("name") or "User"

	bot_reply = await generate_and_persist_bot_reply(
		user_name,
		room_path,
		raw_content,
	)

	logger.info("Sending reply to: %s", target_url)
	await _post_reply(target_url, bot_reply)

	


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks) -> PlainTextResponse:
	payload = await request.json()
	background_tasks.add_task(_process_webhook, payload)
	return PlainTextResponse("OK", status_code=200)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT), reload=RELOAD)