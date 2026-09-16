import asyncio
import logging
import mimetypes
from urllib.parse import urlparse
from typing import Any

from agent.hermes import chat_completions
from agent.hermes_logic import build_space_event_message
from bus import dedupe
from bus.queues import SpaceEventQueueItem, space_events_queue
from db.database import SessionLocal
from db.models import SpaceEvent
from helpers.environment import (
    HERMES_EVENT_ATTACHMENT_PREFETCH,
    HERMES_EVENT_FILE_UPLOAD_ENABLED,
    HERMES_EVENT_FILE_URL_FALLBACK,
    HERMES_EVENT_MAX_ATTACHMENTS,
    HERMES_EVENT_MAX_ATTACHMENT_BYTES,
    SPACE_EVENT_FIRE_AND_FORGET,
    SPACE_EVENT_HERMES_TIMEOUT,
    SPACE_EVENT_MERGE_SETTLE_SECONDS,
)
from space.api.messages import download_attachment_by_id, download_message_attachment
import httpx
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _collect_candidate_attachment_rows(value: Any, rows: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        rows.append(value)
        for nested_value in value.values():
            _collect_candidate_attachment_rows(nested_value, rows)
    elif isinstance(value, list):
        for item in value:
            _collect_candidate_attachment_rows(item, rows)


def _coerce_identifier(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_attachment_url(item: dict[str, Any]) -> str | None:
    for key in ("attachment_url", "file_url", "download_url", "url", "href", "src"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            candidate = value.strip()
            parsed = urlparse(candidate)
            if parsed.scheme in {"http", "https"}:
                return candidate
    return None


def _extract_event_attachments(event_data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not event_data:
        return []

    candidate_rows: list[dict[str, Any]] = []
    _collect_candidate_attachment_rows(event_data, candidate_rows)

    attachments: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()

    for item in candidate_rows:
        url = _extract_attachment_url(item)
        message_id = _coerce_identifier(item.get("message_id") or item.get("id"))
        has_attachment = bool(item.get("has_attachment"))
        if not url and not has_attachment:
            continue

        room_id = _coerce_identifier(item.get("room_id"))
        project_id = _coerce_identifier(item.get("project_id"))
        mime_type = _coerce_identifier(
            item.get("attachment_content_type")
            or item.get("content_type")
            or item.get("mime_type")
        ) or "application/octet-stream"
        filename = _coerce_identifier(item.get("attachment_filename") or item.get("filename") or item.get("name"))
        if filename is None and url:
            parsed = urlparse(url)
            filename = parsed.path.split("/")[-1] or None

        key = (url, message_id, room_id)
        if key in seen:
            continue
        seen.add(key)

        attachments.append(
            {
                "url": url,
                "message_id": message_id,
                "room_id": room_id,
                "project_id": project_id,
                "mime_type": mime_type,
                "filename": filename or "attachment",
            }
        )
        if len(attachments) >= HERMES_EVENT_MAX_ATTACHMENTS:
            break

    return attachments


def _build_attachment_reference_summary(attachments: list[dict[str, Any]]) -> str:
    if not attachments:
        return ""

    lines = ["", "Attachments:"]
    for index, item in enumerate(attachments, start=1):
        filename = item.get("filename") or "attachment"
        mime_type = item.get("mime_type") or "application/octet-stream"
        url = item.get("url")
        if isinstance(url, str) and url:
            lines.append(f"{index}. {filename} ({mime_type}) -> {url}")
        else:
            message_id = item.get("message_id") or "unknown"
            room_id = item.get("room_id") or "unknown"
            lines.append(f"{index}. {filename} ({mime_type}) -> message_id={message_id}, room_id={room_id}")
    return "\n".join(lines)


async def _download_attachment_from_space_api(item: dict[str, Any]) -> bytes | None:
    message_id = item.get("message_id")
    if message_id is None:
        return None

    room_id = item.get("room_id")
    project_id = item.get("project_id")

    try:
        if room_id is not None:
            return await download_message_attachment(project_id, room_id, message_id)
        return await download_attachment_by_id(message_id)
    except Exception as exc:
        logger.warning("Space attachment prefetch failed for message_id=%s: %s", message_id, exc)
        return None


async def _download_attachment_from_url(item: dict[str, Any]) -> bytes | None:
    url = item.get("url")
    if not isinstance(url, str) or not url:
        return None

    try:
        async with httpx.AsyncClient(timeout=SPACE_EVENT_HERMES_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except Exception as exc:
        logger.warning("Attachment URL prefetch failed for url=%s: %s", url, exc)
        return None


async def _prepare_file_uploads(
    attachments: list[dict[str, Any]],
) -> tuple[dict[str, tuple[str, bytes, str]], list[dict[str, Any]]]:
    files: dict[str, tuple[str, bytes, str]] = {}
    unresolved: list[dict[str, Any]] = []

    for index, item in enumerate(attachments, start=1):
        payload: bytes | None = None

        if HERMES_EVENT_ATTACHMENT_PREFETCH:
            payload = await _download_attachment_from_space_api(item)
            if payload is None:
                payload = await _download_attachment_from_url(item)

        if payload is None:
            unresolved.append(item)
            continue

        if len(payload) > HERMES_EVENT_MAX_ATTACHMENT_BYTES:
            logger.warning(
                "Skipping attachment %s: %s bytes exceeds limit %s",
                item.get("filename"),
                len(payload),
                HERMES_EVENT_MAX_ATTACHMENT_BYTES,
            )
            unresolved.append(item)
            continue

        filename = str(item.get("filename") or f"attachment-{index}")
        mime_type = str(item.get("mime_type") or mimetypes.guess_type(filename)[0] or "application/octet-stream")
        files[f"file_{index}"] = (filename, payload, mime_type)

    return files, unresolved


def _log_detached_task_result(task: asyncio.Task[Any]) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.error("Detached task crashed: %s", exc)


async def _send_to_hermes(
    payload: dict[str, Any],
    *,
    profile: str,
    files: dict[str, tuple[str, bytes, str]] | None = None,
    session_id: str | None = None,
    session_key: str | None = None,
    timeout: float | None = SPACE_EVENT_HERMES_TIMEOUT,
) -> dict[str, Any]:
    """Low-level wrapper around agent.hermes.chat_completions."""
    return await chat_completions(
        payload,
        files=files,
        session_id=session_id,
        session_key=session_key,
        profile=profile,
        timeout=timeout,
    )


async def _run_space_event_and_update(
    item: SpaceEventQueueItem,
    space_event: SpaceEvent,
    db: Session,
) -> dict[str, Any]:
    """Build a chat payload from the Space event, run it, and update the DB row.

    All stored members of the event's routing unit (see bus/dedupe.py) are merged into
    one payload here, so a Rails event group results in exactly one Hermes call - and
    the members are marked handled together with that single result.
    """
    group_rows = dedupe.resolve_group_events(db, dedupe_key=item.dedupe_key, fallback=space_event)
    event_type, event_data = dedupe.merge_group_events(
        group_rows,
        fallback_event_type=item.event_type,
        fallback_event_data=item.event_data,
    )

    if len(group_rows) > 1:
        logger.info(
            "[Space Event Dedupe] dispatch key=%s members=%s merged_event_type=%s",
            item.dedupe_key,
            [row.id for row in group_rows],
            event_type,
        )

    message_content = build_space_event_message(
        event_type=event_type,
        event_data=event_data,
    )

    attachments = _extract_event_attachments(event_data)
    upload_files: dict[str, tuple[str, bytes, str]] | None = None
    unresolved_attachments: list[dict[str, Any]] = attachments

    if attachments and HERMES_EVENT_FILE_UPLOAD_ENABLED:
        upload_files, unresolved_attachments = await _prepare_file_uploads(attachments)
        if upload_files:
            logger.info("Prepared %s attachment(s) for Hermes multipart upload", len(upload_files))

    if unresolved_attachments and HERMES_EVENT_FILE_URL_FALLBACK:
        message_content = f"{message_content}\n{_build_attachment_reference_summary(unresolved_attachments)}"

    payload = {
        "messages": [
            {
                "role": "user",
                "content": message_content,
            }
        ]
    }

    response = await _send_to_hermes(payload, profile=item.profile, files=upload_files)

    dedupe.record_group_dispatch(
        db,
        dedupe_key=item.dedupe_key,
        rows=group_rows,
        lead_row_id=space_event.id,
        result_payload=response,
        event_type=event_type,
    )

    return response


def _mark_space_event_failure(
    db: Session,
    space_event: SpaceEvent,
    exc: Exception,
    *,
    dedupe_key: str | None = None,
) -> None:
    error_payload = {
        "status": "error",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }
    rows = dedupe.resolve_group_events(db, dedupe_key=dedupe_key, fallback=space_event)
    dedupe.record_group_failure(db, dedupe_key=dedupe_key, rows=rows, error_payload=error_payload)


def _load_space_event(db: Session, input_data: SpaceEventQueueItem) -> SpaceEvent | None:
    """Resolve the stored row of a queued item.

    The internal row id wins: ``space_event_id`` is the Rails event id, which is not
    unique here (a replayed webhook keeps the id of the original delivery), so resolving
    by it alone can pick the wrong row of a replayed pair.
    """
    if input_data.space_event_row_id is not None:
        row = db.get(SpaceEvent, input_data.space_event_row_id)
        if row is not None:
            return row

    return (
        db.query(SpaceEvent)
        .filter(SpaceEvent.space_event_id == input_data.space_event_id)
        .order_by(SpaceEvent.id)
        .first()
    )


def _skip_if_unit_already_dispatched(db: Session, item: SpaceEventQueueItem, space_event: SpaceEvent) -> bool:
    """Exactly-once guard: never route a member of an already dispatched unit.

    Rows stored before the dedupe feature carry no key, so the key is derived from the
    row when the queue item has none - which is what makes a legacy pair that is still
    in flight collapse into the dispatch that already happened.
    """
    dedupe_key = item.dedupe_key or dedupe.dedupe_key_for_row(space_event)
    if not dedupe_key:
        return False

    dispatched_row_id = dedupe.unit_already_dispatched(
        db,
        dedupe_key=dedupe_key,
        exclude_row_id=space_event.id,
    )
    if dispatched_row_id is None:
        return False

    logger.warning(
        "[Space Event Dedupe] skipping space_event_id=%s: routing unit %s was already dispatched by row=%s",
        space_event.space_event_id,
        dedupe_key,
        dispatched_row_id,
    )
    dedupe.mark_already_dispatched(
        db,
        space_event,
        dedupe_key=dedupe_key,
        dispatched_row_id=dispatched_row_id,
    )
    return True


async def _run_space_event_detached(input_data: SpaceEventQueueItem) -> None:
    """Detached worker used by fire-and-forget mode."""
    db = SessionLocal()
    try:
        space_event = _load_space_event(db, input_data)

        if space_event is None:
            logger.error("SpaceEvent not found for detached space_event_id=%s", input_data.space_event_id)
            return

        if _skip_if_unit_already_dispatched(db, input_data, space_event):
            return

        try:
            await _run_space_event_and_update(input_data, space_event, db)
        except Exception as exc:
            logger.exception("Detached Hermes call failed for space_event id=%s", space_event.id)
            _mark_space_event_failure(db, space_event, exc, dedupe_key=input_data.dedupe_key)
    finally:
        db.close()


async def _defer_while_group_settles(input_data: SpaceEventQueueItem) -> bool:
    """Re-queue a claimed message group until its merge window has closed.

    Members of a Rails event group arrive as independent webhooks, so dispatching the
    first one immediately can drop what the siblings add (``bot_user_ids`` only travels
    on ``ai_question_asked``). The item is put back on the queue and retried on a later
    cron tick; single events are never deferred.
    """
    if not dedupe.key_needs_settle(input_data.dedupe_key) or SPACE_EVENT_MERGE_SETTLE_SECONDS <= 0:
        return False

    db = SessionLocal()
    try:
        settling = dedupe.group_is_settling(
            db,
            input_data.dedupe_key,
            settle_seconds=SPACE_EVENT_MERGE_SETTLE_SECONDS,
        )
    finally:
        db.close()

    if not settling:
        return False

    logger.info(
        "[Space Event Dedupe] merge window still open for key=%s (space_event_id=%s); will dispatch next tick",
        input_data.dedupe_key,
        input_data.space_event_id,
    )
    await space_events_queue.put(input_data)
    return True


async def run_space_event(input_data: SpaceEventQueueItem) -> dict[str, Any] | None:
    """Load a Space event from the DB and forward it to Hermes chat completions."""
    if await _defer_while_group_settles(input_data):
        return {"status": "deferred_merge_window", "dedupe_key": input_data.dedupe_key}

    if SPACE_EVENT_FIRE_AND_FORGET:
        logger.info("Dispatching space_event_id=%s in fire-and-forget mode", input_data.space_event_id)
        task = asyncio.create_task(
            _run_space_event_detached(input_data),
            name=f"space-event-{input_data.space_event_id or 'unknown'}",
        )
        task.add_done_callback(_log_detached_task_result)
        return {"status": "dispatched", "fire_and_forget": True}

    db = SessionLocal()
    try:
        space_event = _load_space_event(db, input_data)

        if space_event is None:
            logger.error("SpaceEvent not found for space_event_id=%s", input_data.space_event_id)
            return None

        if _skip_if_unit_already_dispatched(db, input_data, space_event):
            return {"status": "skipped_already_dispatched", "dedupe_key": input_data.dedupe_key}

        try:
            return await _run_space_event_and_update(input_data, space_event, db)
        except Exception as exc:
            logger.exception("Hermes call failed for space_event id=%s", space_event.id)
            _mark_space_event_failure(db, space_event, exc, dedupe_key=input_data.dedupe_key)
            return None
    finally:
        db.close()


async def submit_space_event(input_data: SpaceEventQueueItem) -> None:
    await space_events_queue.put(input_data)