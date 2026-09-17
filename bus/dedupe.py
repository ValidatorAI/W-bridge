"""Transport-level dedupe for W-space events (one user action => one dispatch).

Why this exists
---------------
Rails emits a user action as a *group* of space events and delivers every member of the
group to the bridge as an independent webhook. For a message that addresses a bot the
group is (``app/controllers/messages_controller.rb#record_created_message_events``)::

    message_created               (always)
    message_attachment_uploaded   (only when the message carries a file)
    ai_question_asked             (only when the message addresses bot users)

All members share ``group_id`` and ``event_id`` (the Rails message id), and each one is
posted on its own by ``OutputEvents::DeliverJob`` (order and timing not guaranteed).
Nothing in the bridge used to key on that, so every member was drained as independent
work: space_events 29 + 30 (room 10, message 31) produced two routing cards
(t_1fd15067, t_81305c75) and two room replies (messages 33 and 35).

Dedupe key (explicit, documented)
---------------------------------
Two shapes, both self-describing (the family is the first segment of the key)::

    # one routing unit per user message - collapses message_created,
    # message_attachment_uploaded and ai_question_asked of the same message
    "message:<group_id>:<room_id>:<message_id>"

    # exact re-delivery of any other event (Rails retries a delivery, duplicated
    # webhook, double ingest) - the payload identity, not the group
    "event:<event_type>:<rails_event_id>:<sha256(event_data)[:16]>"

* ``group_id``  - Rails group of the originating user action (one per action). For the
  message family it is what pairs ``message_created`` with ``ai_question_asked``.
* ``event_id``  - Rails message id; identical for every member of a message group and
  used as the message id when ``event_data`` does not carry one explicitly.
* ``message``   - only the message-addressed event types (``MESSAGE_EVENT_TYPES``) are
  collapsed this way. Rooms/account groups reuse ``(group_id, event_id)`` for several
  *distinct* facts (space_events 31+32: ``account_settings_updated`` +
  ``account_bot_access_updated`` at 03:12:13Z share group ``c5c19ed2``; space_events
  19-22: ``room_created`` + ``direct_conversation_created`` + two ``room_member_added``
  share group ``9625ee39`` and event id 10). Collapsing those would silently drop real
  events, so they are keyed by payload identity instead, which only drops a byte
  identical re-delivery of the same Rails event.
* ``message_id`` keeps two genuinely distinct user messages in the same room apart:
  different messages get different keys and are both dispatched (no regression).

Dedupe mechanics
----------------
1. Ingest (``main.py``): the event row is stored with its ``dedupe_key`` and the key is
   *claimed* by inserting into ``space_event_dispatch_groups``, whose ``dedupe_key`` is
   UNIQUE. Exactly one member of a group wins that insert and only that member is
   queued. The loser is recorded on its own row (``result.status = "duplicate_merged"``)
   and logged as a duplicate; it is never queued, so a later drain cannot re-route it.
2. Drain (``bus/executors.py``): a message group waits out a short settle window
   (``SPACE_EVENT_MERGE_SETTLE_SECONDS``) so members delivered by separate Rails jobs
   are already stored, then all member rows of the key are merged into ONE event
   payload (``merge_group_events``) and sent as a single Hermes call. Every member row
   is marked handled in the same commit (``record_group_dispatch``).

One dispatch artifact per addressed bot: the merge keeps ``bot_user_ids`` (which only
``ai_question_asked`` carries) in the payload of the single dispatch, so the routing
layer sees the addressed bots exactly once. A group addressed to several bots still
produces one dispatch that carries all of them - the per-bot fan-out is assignee
selection and is deliberately untouched here.

Safety net: ``pending_dispatch_items`` re-queues work that the in-memory queue would
otherwise lose across a restart (claimed groups and un-dispatched event rows from the
recent past), so a claimed group can never be swallowed by its own claim.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bus.queues import SpaceEventQueueItem
from db.database import SessionLocal
from db.models import SpaceEvent, SpaceEventDispatchGroup
from helpers.environment import BASE_HERMES_PROFILE, SPACE_EVENT_LEGACY_DISPATCH_LOOKBACK_SECONDS

logger = logging.getLogger(__name__)

# Event types that belong to the "one user message" routing unit.
MESSAGE_EVENT_TYPES = frozenset({"message_created", "message_attachment_uploaded", "ai_question_asked"})
# The member that carries the addressed bots; also the event type of the merged payload.
ROUTING_EVENT_TYPE = "ai_question_asked"

DEDUPE_FAMILY_MESSAGE = "message"
DEDUPE_FAMILY_EVENT = "event"

# Duplicate members of an already-claimed group are recorded with this status.
DUPLICATE_STATUS = "duplicate_merged"

GROUP_STATUS_PENDING = "pending"
GROUP_STATUS_DISPATCHED = "dispatched"
GROUP_STATUS_FAILED = "failed"

# Payload overlay order, lowest authority first: the routing event (ai_question_asked)
# wins on conflicting keys, so the merged payload keeps the bot addressing.
_PAYLOAD_PRIORITY = ("message_attachment_uploaded", "message_created", "ai_question_asked")


@dataclass(frozen=True)
class DedupeDecision:
    """Outcome of claiming a routing unit for a freshly stored space event."""

    dedupe_key: str | None
    is_duplicate: bool
    group_row_id: int | None = None
    duplicate_of_space_event_id: str | None = None


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _event_data_of(payload: dict[str, Any] | None) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _message_id_of(event_data: dict[str, Any], event_id: Any) -> str | None:
    content_payload = event_data.get("content_payload")
    if isinstance(content_payload, dict):
        message_id = _as_text(content_payload.get("message_id"))
        if message_id:
            return message_id
    message_id = _as_text(event_data.get("message_id"))
    if message_id:
        return message_id
    # Message events carry the Rails message id in `event_id` (see the Rails emitter).
    return _as_text(event_id)


def _payload_fingerprint(event_data: dict[str, Any]) -> str:
    canonical = json.dumps(event_data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def key_family(dedupe_key: str | None) -> str | None:
    """Return the family segment of a dedupe key ("message" / "event"), if any."""
    if not dedupe_key:
        return None
    family, _, _rest = dedupe_key.partition(":")
    return family or None


def key_group(dedupe_key: str | None) -> str | None:
    """Return the Rails group id carried by a key ("message:<group_id>:<room>:<msg>")."""
    if key_family(dedupe_key) != DEDUPE_FAMILY_MESSAGE:
        return None
    _family, _, rest = dedupe_key.partition(":")
    group_id, _, _rest = rest.partition(":")
    return group_id or None


def key_needs_settle(dedupe_key: str | None) -> bool:
    """Only message groups have several members to wait for; single events do not."""
    return key_family(dedupe_key) == DEDUPE_FAMILY_MESSAGE


def build_dedupe_key(
    *,
    event_type: Any,
    group_id: Any,
    event_data: dict[str, Any] | None,
    event_id: Any = None,
    space_event_id: Any = None,
) -> str | None:
    """Build the explicit dedupe key of an incoming space event (None = never deduped).

    See the module docstring for the key shapes and why the keys are scoped this way.
    """
    normalized_type = _as_text(event_type)
    if normalized_type is None:
        # Without an event type we cannot prove anything about identity.
        return None

    data = _event_data_of(event_data)
    normalized_group = _as_text(group_id)

    if normalized_type in MESSAGE_EVENT_TYPES and normalized_group:
        room_id = _as_text(data.get("room_id"))
        message_id = _message_id_of(data, event_id)
        if room_id and message_id:
            return f"{DEDUPE_FAMILY_MESSAGE}:{normalized_group}:{room_id}:{message_id}"

    identity = _as_text(space_event_id) or _as_text(event_id) or "-"
    return f"{DEDUPE_FAMILY_EVENT}:{normalized_type}:{identity}:{_payload_fingerprint(data)}"


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def claim_dispatch_group(
    *,
    dedupe_key: str | None,
    row_id: int | None,
    space_event_id: str | None,
) -> DedupeDecision:
    """Claim the routing unit of a freshly stored space event.

    The UNIQUE constraint on ``space_event_dispatch_groups.dedupe_key`` is the lock: the
    first member of the unit inserts the claim row and owns the dispatch, every later
    member fails the insert and is recorded as a duplicate instead of being queued.
    """
    if dedupe_key is None:
        return DedupeDecision(dedupe_key=None, is_duplicate=False)

    if row_id is None:
        # The event row could not be stored, so the group could not be resolved at drain
        # time; fall back to the historical (undeduped) path instead of losing the event.
        logger.error(
            "[Space Event Dedupe] no stored row for space_event_id=%s key=%s; skipping claim",
            space_event_id,
            dedupe_key,
        )
        return DedupeDecision(dedupe_key=None, is_duplicate=False)

    db = SessionLocal()
    try:
        group = SpaceEventDispatchGroup(
            dedupe_key=dedupe_key,
            lead_space_event_id=space_event_id,
            lead_space_event_row_id=row_id,
            status=GROUP_STATUS_PENDING,
        )
        db.add(group)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return _record_duplicate_member(db, dedupe_key=dedupe_key, row_id=row_id, space_event_id=space_event_id)

        logger.info(
            "[Space Event Dedupe] claimed key=%s owner_space_event_id=%s row=%s",
            dedupe_key,
            space_event_id,
            row_id,
        )
        return DedupeDecision(dedupe_key=dedupe_key, is_duplicate=False, group_row_id=group.id)
    finally:
        db.close()


def _record_duplicate_member(
    db: Session,
    *,
    dedupe_key: str,
    row_id: int,
    space_event_id: str | None,
) -> DedupeDecision:
    """Mark a member of an already-claimed group as duplicate; never queue it."""
    group = db.query(SpaceEventDispatchGroup).filter(
        SpaceEventDispatchGroup.dedupe_key == dedupe_key
    ).first()

    row = db.get(SpaceEvent, row_id)
    if row is not None:
        _mark_row_duplicate(
            db,
            row,
            dedupe_key=dedupe_key,
            dispatched_row_id=None,
            dispatched_space_event_id=group.lead_space_event_id if group else None,
        )

    logger.info(
        "[Space Event Dedupe] duplicate space_event_id=%s key=%s dispatch_owner=%s (not queued)",
        space_event_id,
        dedupe_key,
        group.lead_space_event_id if group else None,
    )
    return DedupeDecision(
        dedupe_key=dedupe_key,
        is_duplicate=True,
        group_row_id=group.id if group else None,
        duplicate_of_space_event_id=group.lead_space_event_id if group else None,
    )


def _mark_row_duplicate(
    db: Session,
    row: SpaceEvent,
    *,
    dedupe_key: str | None,
    dispatched_row_id: int | None,
    dispatched_space_event_id: str | None = None,
    handled: bool = False,
) -> None:
    """Record on a member row that its routing unit was dispatched elsewhere.

    ``handled`` stamps the row as handled too: the member was carried by the unit's
    single dispatch, and a row with a result is never picked up by the restart recovery
    again (which is what used to re-queue the same twin on every server start).
    """
    if dedupe_key and not row.dedupe_key:
        row.dedupe_key = dedupe_key
    row.result = json.dumps(
        {
            "status": DUPLICATE_STATUS,
            "dedupe_key": dedupe_key,
            "dispatch_owner_space_event_id": dispatched_space_event_id,
            "dispatch_owner_row_id": dispatched_row_id,
            "note": (
                "member of a Rails event group that was already dispatched; merged into "
                "that single dispatch instead of being routed again"
            ),
        }
    )
    if handled:
        row.sent_date = func.now()
    _commit(db, context=f"duplicate marker row={row.id}")


def dedupe_key_for_row(row: SpaceEvent) -> str | None:
    """The dedupe key of a stored event row (used for rows stored before this feature)."""
    return build_dedupe_key(
        event_type=row.event_type,
        group_id=row.group_id,
        event_data=row.event_data,
        event_id=row.event_id,
        space_event_id=row.space_event_id,
    )


def _dispatched_sibling(db: Session, dedupe_key: str, *, exclude_row_id: int) -> SpaceEvent | None:
    return (
        db.query(SpaceEvent)
        .filter(
            SpaceEvent.dedupe_key == dedupe_key,
            SpaceEvent.sent_date.isnot(None),
            SpaceEvent.id != exclude_row_id,
        )
        .order_by(SpaceEvent.id)
        .first()
    )


def unit_already_dispatched(
    db: Session,
    *,
    dedupe_key: str | None,
    exclude_row_id: int,
    legacy_lookback_seconds: float | None = None,
) -> int | None:
    """Row id of a member of the same routing unit that was already dispatched.

    This is the "exactly once" guard of the drain loop: a routing unit must produce one
    dispatch, so any later member - including a member re-queued by the restart recovery
    or by a duplicate enqueue - is skipped instead of being routed again.

    Members stored before this feature carry no key. For message units a legacy member of
    the same group is therefore compared by its derived key, but only inside the recent
    lookback window: that is the window in which a lost queue can still be replayed, so
    an event explicitly re-sent after it is treated as new work instead of being silently
    swallowed by a months-old dispatch.
    """
    if not dedupe_key:
        return None

    sibling = _dispatched_sibling(db, dedupe_key, exclude_row_id=exclude_row_id)
    if sibling is not None:
        return sibling.id

    lookback = (
        SPACE_EVENT_LEGACY_DISPATCH_LOOKBACK_SECONDS
        if legacy_lookback_seconds is None
        else legacy_lookback_seconds
    )
    legacy = _legacy_dispatched_sibling(
        db,
        dedupe_key=dedupe_key,
        exclude_row_id=exclude_row_id,
        within_seconds=lookback,
    )
    return legacy.id if legacy else None


def _legacy_dispatched_sibling(
    db: Session,
    *,
    dedupe_key: str,
    exclude_row_id: int,
    within_seconds: float,
) -> SpaceEvent | None:
    """A pre-feature member of the same message unit that was already dispatched."""
    group_id = key_group(dedupe_key)
    if not group_id or within_seconds <= 0:
        return None

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
    candidates = (
        db.query(SpaceEvent)
        .filter(
            SpaceEvent.dedupe_key.is_(None),
            SpaceEvent.sent_date.isnot(None),
            SpaceEvent.sent_date >= cutoff.replace(tzinfo=None),
            SpaceEvent.group_id == group_id,
            SpaceEvent.event_type.in_(tuple(MESSAGE_EVENT_TYPES)),
            SpaceEvent.id != exclude_row_id,
        )
        .order_by(SpaceEvent.id)
        .all()
    )
    for row in candidates:
        if dedupe_key_for_row(row) == dedupe_key:
            return row
    return None


def mark_already_dispatched(
    db: Session,
    row: SpaceEvent,
    *,
    dedupe_key: str,
    dispatched_row_id: int,
) -> None:
    """Record why a member was not dispatched (its unit was already handled)."""
    _mark_row_duplicate(
        db,
        row,
        dedupe_key=dedupe_key,
        dispatched_row_id=dispatched_row_id,
        handled=True,
    )


def resolve_group_events(db: Session, *, dedupe_key: str | None, fallback: SpaceEvent) -> list[SpaceEvent]:
    """All stored members of a routing unit, ordered by ingest order."""
    if not dedupe_key:
        return [fallback]
    rows = (
        db.query(SpaceEvent)
        .filter(SpaceEvent.dedupe_key == dedupe_key)
        .order_by(SpaceEvent.id)
        .all()
    )
    return rows or [fallback]


def group_is_settling(
    db: Session,
    dedupe_key: str | None,
    *,
    settle_seconds: float,
    now: datetime | None = None,
) -> bool:
    """True while the merge window of a claimed message group is still open.

    Members of one Rails group are delivered by independent jobs, so dispatching the
    first one immediately would drop the payload of the siblings (``bot_user_ids`` only
    travels on ``ai_question_asked``). Waiting the window out guarantees the members
    that exist are merged; an event that never gets a sibling is dispatched as before
    once the window closes.
    """
    if not dedupe_key or settle_seconds <= 0 or not key_needs_settle(dedupe_key):
        return False

    group = db.query(SpaceEventDispatchGroup).filter(
        SpaceEventDispatchGroup.dedupe_key == dedupe_key
    ).first()
    if group is None or group.status != GROUP_STATUS_PENDING:
        return False

    created_at = _as_utc(group.created_at)
    if created_at is None:
        return False

    reference = now or datetime.now(timezone.utc)
    return reference - created_at < timedelta(seconds=settle_seconds)


def _payload_rank(event_type: Any) -> int:
    normalized = _as_text(event_type)
    try:
        return _PAYLOAD_PRIORITY.index(normalized)
    except ValueError:
        return len(_PAYLOAD_PRIORITY)


def _union_lists(base: list[Any], overlay: list[Any]) -> list[Any]:
    merged = list(base)
    for item in overlay:
        if item not in merged:
            merged.append(item)
    return merged


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            merged[key] = _union_lists(current, value)
        elif value is None and current is not None:
            continue
        else:
            merged[key] = value
    return merged


def merge_group_events(
    rows: Sequence[SpaceEvent],
    *,
    fallback_event_type: str | None = None,
    fallback_event_data: dict[str, Any] | None = None,
) -> tuple[str | None, dict[str, Any] | None]:
    """Merge every member of one routing unit into a single (event_type, event_data).

    The members of a message group are near-identical payloads that differ exactly in the
    information their own event type adds (``bot_user_ids`` on ``ai_question_asked``, the
    attachment fields on ``message_attachment_uploaded``). Overlaying them in
    ``_PAYLOAD_PRIORITY`` order (lists unioned) yields one payload with all of it, so the
    single dispatch is at least as informative as any individual member dispatch was.

    ``fallback_*`` is the payload of the webhook that was drained: it is used as the base
    (lowest priority) so a member row that stores no ``event_data`` - or an item that was
    queued by an older bridge version - still dispatches its full payload.
    """
    ordered = sorted(rows, key=lambda row: _payload_rank(row.event_type))

    merged_type: str | None = _as_text(fallback_event_type)
    merged_data: dict[str, Any] = _deep_merge({}, _event_data_of(fallback_event_data))
    for row in ordered:
        merged_data = _deep_merge(merged_data, _event_data_of(row.event_data))
        normalized_type = _as_text(row.event_type)
        if normalized_type == ROUTING_EVENT_TYPE:
            merged_type = ROUTING_EVENT_TYPE
        elif merged_type is None:
            merged_type = normalized_type

    return merged_type, merged_data


def record_group_dispatch(
    db: Session,
    *,
    dedupe_key: str | None,
    rows: Sequence[SpaceEvent],
    lead_row_id: int,
    result_payload: dict[str, Any],
    event_type: str | None,
) -> None:
    """Mark every member of the routing unit handled in one commit (never one by one)."""
    for row in rows:
        row.sent_date = func.now()
        if row.id == lead_row_id:
            row.result = json.dumps(result_payload)
        else:
            row.result = json.dumps(
                {
                    "status": DUPLICATE_STATUS,
                    "dedupe_key": dedupe_key,
                    "dispatch_owner_row_id": lead_row_id,
                    "note": "merged into the single dispatch of this Rails event group",
                }
            )

    group = _load_group(db, dedupe_key)
    if group is not None:
        group.status = GROUP_STATUS_DISPATCHED
        group.dispatched_at = func.now()
        group.result = json.dumps(
            {
                "status": "dispatched",
                "event_type": event_type,
                "member_rows": [row.id for row in rows],
            }
        )

    _commit(db, context=f"group {dedupe_key} dispatch")


def record_group_failure(
    db: Session,
    *,
    dedupe_key: str | None,
    rows: Sequence[SpaceEvent],
    error_payload: dict[str, Any],
) -> None:
    """Mark every member of the routing unit with the same failure payload."""
    serialized = json.dumps(error_payload)
    for row in rows:
        row.result = serialized

    group = _load_group(db, dedupe_key)
    if group is not None and group.status != GROUP_STATUS_DISPATCHED:
        group.status = GROUP_STATUS_FAILED
        group.result = serialized

    _commit(db, context=f"group {dedupe_key} failure")


def _load_group(db: Session, dedupe_key: str | None) -> SpaceEventDispatchGroup | None:
    if not dedupe_key:
        return None
    return db.query(SpaceEventDispatchGroup).filter(
        SpaceEventDispatchGroup.dedupe_key == dedupe_key
    ).first()


def _commit(db: Session, *, context: str) -> None:
    try:
        db.commit()
    except Exception:
        logger.exception("[Space Event Dedupe] commit failed for %s", context)
        db.rollback()


def pending_dispatch_items(*, max_age_seconds: float) -> list[SpaceEventQueueItem]:
    """Work the in-memory queue would lose across a restart.

    * claimed groups that were never dispatched,
    * stored event rows that were never dispatched and never marked as failed.

    Rows stored before this feature carry no ``dedupe_key``; they are attached to their
    routing unit here (``_backfill_legacy_keys``) so that a pair which is still waiting
    in the queue is recovered as ONE dispatch and a member whose unit was already
    dispatched is skipped instead of being routed a second time. Only rows from the
    recent past are recovered, so a long history is not replayed.
    """
    if max_age_seconds <= 0:
        return []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=max_age_seconds)
    items: list[SpaceEventQueueItem] = []

    db = SessionLocal()
    try:
        window_rows = (
            db.query(SpaceEvent)
            .filter(SpaceEvent.stored_date >= cutoff.replace(tzinfo=None))
            .order_by(SpaceEvent.id)
            .all()
        )
        _backfill_legacy_keys(db, window_rows)

        for row in window_rows:
            if row.sent_date is not None:
                continue

            status = _result_status(row.result)
            if status == DUPLICATE_STATUS:
                # Already merged into the dispatch of its unit: stamp it as handled once
                # that dispatch exists, so it stops being reported as un-dispatched work
                # (and is never re-queued on a later start).
                if row.dedupe_key:
                    dispatched = _dispatched_sibling(db, row.dedupe_key, exclude_row_id=row.id)
                    if dispatched is not None:
                        mark_already_dispatched(
                            db,
                            row,
                            dedupe_key=row.dedupe_key,
                            dispatched_row_id=dispatched.id,
                        )
                continue
            if status is not None:
                # A row that already carries a result was handled (or failed): it must
                # not be re-queued, otherwise every server start re-routes it.
                continue

            if row.dedupe_key:
                dispatched = _dispatched_sibling(db, row.dedupe_key, exclude_row_id=row.id)
                if dispatched is not None:
                    logger.warning(
                        "[Space Event Dedupe] recovery: row=%s key=%s already dispatched by row=%s; not recovered",
                        row.id,
                        row.dedupe_key,
                        dispatched.id,
                    )
                    mark_already_dispatched(
                        db,
                        row,
                        dedupe_key=row.dedupe_key,
                        dispatched_row_id=dispatched.id,
                    )
                    continue

                owner = _load_group(db, row.dedupe_key)
                if owner is None:
                    decision = claim_dispatch_group(
                        dedupe_key=row.dedupe_key,
                        row_id=row.id,
                        space_event_id=row.space_event_id,
                    )
                    if decision.is_duplicate:
                        continue
                    owner = _load_group(db, row.dedupe_key)

                if owner is not None and owner.status == GROUP_STATUS_DISPATCHED:
                    continue
                if owner is not None and _as_text(owner.lead_space_event_id) != _as_text(row.space_event_id):
                    # Another member of the unit is the claimed owner and is queued for
                    # the single dispatch, so this member is only recorded as duplicate.
                    _mark_row_duplicate(
                        db,
                        row,
                        dedupe_key=row.dedupe_key,
                        dispatched_row_id=owner.lead_space_event_row_id,
                        dispatched_space_event_id=owner.lead_space_event_id,
                    )
                    continue

            items.append(
                SpaceEventQueueItem(
                    space_event_id=row.space_event_id,
                    event_type=row.event_type,
                    event_data=row.event_data,
                    dedupe_key=row.dedupe_key,
                    space_event_row_id=row.id,
                )
            )
    finally:
        db.close()

    return items


def _backfill_legacy_keys(db: Session, rows: Sequence[SpaceEvent]) -> None:
    """Attach a dedupe key to rows stored before the feature existed."""
    changed = False
    for row in rows:
        if row.dedupe_key:
            continue
        key = dedupe_key_for_row(row)
        if not key:
            continue
        row.dedupe_key = key
        changed = True
        logger.info(
            "[Space Event Dedupe] backfilled dedupe_key=%s on legacy row=%s (space_event_id=%s)",
            key,
            row.id,
            row.space_event_id,
        )
    if changed:
        _commit(db, context="legacy dedupe key backfill")


def _result_status(result: str | None) -> str | None:
    if not result:
        return None
    try:
        parsed = json.loads(result)
    except (TypeError, ValueError):
        return None
    if isinstance(parsed, dict):
        return _as_text(parsed.get("status"))
    return None
