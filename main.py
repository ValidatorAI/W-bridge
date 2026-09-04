import html
import logging
import re
from typing import Any
import os
import asyncio
import uvicorn
import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from helpers.helpers import str_to_bool
from schemas.pydantic import SpaceEventInput


app = FastAPI()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOM_BASE_URL = os.getenv("ROOM_BASE_URL", "https://chat.nvgtrs.io").rstrip("/")
PORT = os.getenv("PORT", "80")
RELOAD = str_to_bool(os.getenv("RELOAD", "False"))
OUTPUT_EVENTS_TOKEN = os.getenv("OUTPUT_EVENTS_TOKEN")

"""
@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks) -> PlainTextResponse:
	payload = await request.json()
	background_tasks.add_task(_process_webhook, payload)
	return PlainTextResponse("", status_code=200)
"""


@app.post("/space_events")
async def space_events(
	event: SpaceEventInput,
	authorization: str | None = Header(default=None),
) -> PlainTextResponse:
	expected = f"Bearer {OUTPUT_EVENTS_TOKEN}"

	if not OUTPUT_EVENTS_TOKEN or authorization != expected:
		raise HTTPException(status_code=401, detail="Invalid token")

	logger.info("[Space Event Received]: %s", event.model_dump())
	return PlainTextResponse("", status_code=200)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT), reload=RELOAD)