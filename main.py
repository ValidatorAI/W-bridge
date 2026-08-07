import html
import logging
import re
from typing import Any
import os
import uvicorn
import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import PlainTextResponse


app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _strip_html(raw_html: str) -> str:
	no_tags = re.sub(r"<[^>]*>", "", raw_html)
	decoded = html.unescape(no_tags)
	return re.sub(r"\s+", " ", decoded).strip()


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

	target_url = f"https://chat.nvgtrs.io{room_path}"
	cleaned_text = _strip_html(raw_content)
	user_name = (payload.get("user") or {}).get("name") or "User"
	bot_reply = f"🤖 AI Response to {user_name}: I received {cleaned_text}"

	logger.info("Sending reply to: %s", target_url)

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


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks) -> PlainTextResponse:
	payload = await request.json()
	background_tasks.add_task(_process_webhook, payload)
	return PlainTextResponse("OK", status_code=200)

def str_to_bool(value: str) -> bool:
    return value.lower() in {"true", "1", "yes"}

Port = os.getenv("PORT", "4141")
reload = str_to_bool(os.getenv("RELOAD", "False"))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(Port), reload=reload)