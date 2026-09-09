from contextlib import asynccontextmanager
import html
import logging
import os
import re
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from bus.cron import start_cron, stop_cron
from bus.executors import submit_space_event
from bus.queues import SpaceEventQueueItem
from db.database import SessionLocal
from db.models import SpaceEvent
from helpers.helpers import str_to_bool
from mcp.server import handle_mcp_request
from schemas.pydantic import SpaceEventInput


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_cron()
    yield
    await stop_cron()


app = FastAPI(lifespan=lifespan)

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

	space_event_id = str(event.id) if event.id is not None else None
	_db_persist_space_event(event)

	await submit_space_event(
		SpaceEventQueueItem(
			space_event_id=space_event_id,
			event_type=event.event_type,
			event_data=event.event_data,
		)
	)

	return PlainTextResponse("", status_code=200)


def _db_persist_space_event(event: SpaceEventInput) -> None:
	"""Persist the incoming Space event; errors are logged, not raised."""
	db = SessionLocal()
	try:
		db_event = SpaceEvent(
			space_event_id=str(event.id) if event.id is not None else None,
			event_type=event.event_type,
			event_id=str(event.event_id) if event.event_id is not None else None,
			group_id=event.group_id,
			event_data=event.event_data,
			created_at=event.created_at,
		)
		db.add(db_event)
		db.commit()
	except Exception:
		logger.exception("Failed to persist Space event id=%s", event.id)
		db.rollback()
	finally:
		db.close()


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
	try:
		payload = await request.json()
	except Exception:
		return JSONResponse(
			status_code=400,
			content={
				"jsonrpc": "2.0",
				"id": None,
				"error": {"code": -32700, "message": "Parse error: invalid JSON"},
			},
		)

	response_data = await handle_mcp_request(payload)
	if response_data is None:
		return Response(status_code=204)
	return JSONResponse(content=response_data)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT), reload=RELOAD)