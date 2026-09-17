"""Transport dedupe of Rails event groups (bus/dedupe.py + ingest/drain wiring).

The payloads below are the real space_events 63/64 pair that produced two cards and two
room replies in room 10 (group 4fd1efe2, message 31): message_created and
ai_question_asked of the SAME user message, delivered as two independent webhooks.
"""

import contextlib
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bus import dedupe
from bus.queues import SpaceEventQueueItem, space_events_queue
from db.database import Base
from db.models import SpaceEvent, SpaceEventDispatchGroup
from main import app

GROUP_ID = "4fd1efe2-e6e3-46d9-811d-7f7894c7c671"
ROOM_ID = 10
MESSAGE_ID = 31
INCIDENT_DEDUPE_KEY = f"{dedupe.DEDUPE_FAMILY_MESSAGE}:{GROUP_ID}:{ROOM_ID}:{MESSAGE_ID}"

ACTOR = {
    "type": "User",
    "id": 1,
    "username": "siavash mohammady",
    "full_name": "siavash mohammady",
}


def _message_payload(event_id, event_type, *, bot_user_ids=None):
    content_payload = {
        "type": "message",
        "message_id": MESSAGE_ID,
        "room_id": ROOM_ID,
        "content_type": "text",
        "text": "what about business canvas?",
    }
    if bot_user_ids is not None:
        content_payload["bot_user_ids"] = bot_user_ids

    event_data = {
        "room_id": ROOM_ID,
        "content_type": "text",
        "actor": ACTOR,
        "target_type": "Message",
        "occurred_at": "2026-09-16T03:03:03Z",
        "content": "what about business canvas?",
        "content_payload": content_payload,
    }
    if bot_user_ids is not None:
        event_data["bot_user_ids"] = bot_user_ids

    return {
        "id": event_id,
        "event_type": event_type,
        "event_id": MESSAGE_ID,
        "group_id": GROUP_ID,
        "event_data": event_data,
        "created_at": "2026-09-16T03:03:03Z",
    }


INCIDENT_MESSAGE_CREATED = _message_payload(63, "message_created")
INCIDENT_AI_QUESTION_ASKED = _message_payload(64, "ai_question_asked", bot_user_ids=[7])


def _account_event(space_event_id, event_type, *, group_id, occurred_at, allowed_bot_user_ids=None, removed=None):
    event_data = {
        "actor": ACTOR,
        "target_type": "User",
        "occurred_at": occurred_at,
        "content": "Account settings updated",
        "content_payload": {"type": "message"},
    }
    if allowed_bot_user_ids is not None:
        event_data["allowed_bot_user_ids"] = allowed_bot_user_ids
    if removed is not None:
        event_data["removed_bot_user_ids"] = removed
    return {
        "id": space_event_id,
        "event_type": event_type,
        "event_id": 1,
        "group_id": group_id,
        "event_data": event_data,
        "created_at": occurred_at,
    }


@contextlib.contextmanager
def _isolated_bridge_db(tmp_path):
    """Point the app, the dedupe layer and the drain loop at a throwaway SQLite DB."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'dedupe_test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with (
        patch("main.SessionLocal", factory),
        patch("bus.dedupe.SessionLocal", factory),
        patch("bus.executors.SessionLocal", factory),
        patch("main.OUTPUT_EVENTS_TOKEN", "test-token"),
    ):
        yield factory


def _post(client, payload):
    return client.post(
        "/space_events",
        json=payload,
        headers={"Authorization": "Bearer test-token"},
    )


def _queued_items():
    """Items actually handed to the queue by the ingest endpoint."""
    return _RECORDED_QUEUE_ITEMS


_RECORDED_QUEUE_ITEMS: list[SpaceEventQueueItem] = []


@contextlib.contextmanager
def _record_dispatch_queue():
    """Record the ingest -> queue handoff instead of touching the real asyncio queue."""

    async def _record(item):
        _RECORDED_QUEUE_ITEMS.append(item)

    _RECORDED_QUEUE_ITEMS.clear()
    with patch("main.submit_space_event", _record):
        yield _RECORDED_QUEUE_ITEMS
    _RECORDED_QUEUE_ITEMS.clear()


def _rows(factory):
    db = factory()
    try:
        return db.query(SpaceEvent).order_by(SpaceEvent.id).all()
    finally:
        db.close()


def _groups(factory):
    db = factory()
    try:
        return db.query(SpaceEventDispatchGroup).all()
    finally:
        db.close()


# ---------------------------------------------------------------- key construction


def test_message_group_members_share_one_key():
    """message_created and ai_question_asked of one message are one routing unit."""
    created = dedupe.build_dedupe_key(
        event_type=INCIDENT_MESSAGE_CREATED["event_type"],
        group_id=INCIDENT_MESSAGE_CREATED["group_id"],
        event_data=INCIDENT_MESSAGE_CREATED["event_data"],
        event_id=INCIDENT_MESSAGE_CREATED["event_id"],
        space_event_id=INCIDENT_MESSAGE_CREATED["id"],
    )
    asked = dedupe.build_dedupe_key(
        event_type=INCIDENT_AI_QUESTION_ASKED["event_type"],
        group_id=INCIDENT_AI_QUESTION_ASKED["group_id"],
        event_data=INCIDENT_AI_QUESTION_ASKED["event_data"],
        event_id=INCIDENT_AI_QUESTION_ASKED["event_id"],
        space_event_id=INCIDENT_AI_QUESTION_ASKED["id"],
    )

    assert created == asked == INCIDENT_DEDUPE_KEY


def test_distinct_messages_in_the_same_room_get_distinct_keys():
    """AC5: a second, genuinely different user message is its own routing unit."""
    other_group = "a07b309c-5a57-4c63-ba45-383390713384"
    other = _message_payload(999, "message_created")
    other["group_id"] = other_group
    other["event_id"] = 32
    other["event_data"]["content_payload"]["message_id"] = 32

    key = dedupe.build_dedupe_key(
        event_type=other["event_type"],
        group_id=other["group_id"],
        event_data=other["event_data"],
        event_id=other["event_id"],
        space_event_id=other["id"],
    )

    assert key == f"{dedupe.DEDUPE_FAMILY_MESSAGE}:{other_group}:{ROOM_ID}:32"
    assert key != INCIDENT_DEDUPE_KEY


def test_distinct_account_events_in_one_group_are_not_collapsed():
    """Rails reuses (group_id, event_id) for distinct facts - they must survive."""
    settings = _account_event(65, "account_settings_updated", group_id="c5c19ed2-group", occurred_at="2026-09-16T03:12:13Z")
    access = _account_event(
        66,
        "account_bot_access_updated",
        group_id="c5c19ed2-group",
        occurred_at="2026-09-16T03:12:13Z",
        allowed_bot_user_ids=[2, 4],
    )

    def key(payload):
        return dedupe.build_dedupe_key(
            event_type=payload["event_type"],
            group_id=payload["group_id"],
            event_data=payload["event_data"],
            event_id=payload["event_id"],
            space_event_id=payload["id"],
        )

    assert key(settings) != key(access)
    assert key(settings).startswith(f"{dedupe.DEDUPE_FAMILY_EVENT}:account_settings_updated:65:")


def test_byte_identical_redelivery_of_an_event_shares_a_key():
    """A Rails redelivery of the same event is the same routing unit."""
    payload = _account_event(67, "project_member_added", group_id=None, occurred_at="2026-09-16T03:12:51Z")
    payload["event_id"] = None

    def key(item):
        return dedupe.build_dedupe_key(
            event_type=item["event_type"],
            group_id=item["group_id"],
            event_data=item["event_data"],
            event_id=item["event_id"],
            space_event_id=item["id"],
        )

    assert key(payload) == key(payload)
    assert key(payload) is not None

    changed = _account_event(67, "project_member_added", group_id=None, occurred_at="2026-09-16T03:12:52Z")
    changed["event_id"] = None
    assert key(changed) != key(payload)


# ---------------------------------------------------------------- payload merging


def test_merge_keeps_bot_addressing_and_content_of_every_member():
    created = SpaceEvent(
        id=1,
        space_event_id="63",
        event_type="message_created",
        group_id=GROUP_ID,
        event_data=INCIDENT_MESSAGE_CREATED["event_data"],
    )
    asked = SpaceEvent(
        id=2,
        space_event_id="64",
        event_type="ai_question_asked",
        group_id=GROUP_ID,
        event_data=INCIDENT_AI_QUESTION_ASKED["event_data"],
    )

    event_type, event_data = dedupe.merge_group_events([created, asked])

    assert event_type == "ai_question_asked"
    assert event_data["bot_user_ids"] == [7]
    assert event_data["content"] == "what about business canvas?"
    assert event_data["content_payload"]["message_id"] == MESSAGE_ID


def test_merge_unions_bot_lists_and_keeps_attachment_fields():
    attachment = SpaceEvent(
        id=3,
        space_event_id="65",
        event_type="message_attachment_uploaded",
        event_data={"room_id": ROOM_ID, "filename": "canvas.pdf", "content": None},
    )
    asked = SpaceEvent(
        id=4,
        space_event_id="66",
        event_type="ai_question_asked",
        event_data={"room_id": ROOM_ID, "bot_user_ids": [7], "content": "see file"},
    )

    event_type, event_data = dedupe.merge_group_events([asked, attachment])

    assert event_type == "ai_question_asked"
    assert event_data["bot_user_ids"] == [7]
    assert event_data["filename"] == "canvas.pdf"
    assert event_data["content"] == "see file"


# ---------------------------------------------------------------- ingest (AC1/AC3)


def test_one_user_message_yields_exactly_one_queued_dispatch(tmp_path):
    """AC1/AC4: replaying the incident pair queues ONE item, not two."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        assert _post(client, INCIDENT_MESSAGE_CREATED).status_code == 200
        assert _post(client, INCIDENT_AI_QUESTION_ASKED).status_code == 200

        assert len(queued) == 1
        assert queued[0].dedupe_key == INCIDENT_DEDUPE_KEY
        assert queued[0].space_event_id == "63"

        rows = _rows(factory)
        assert len(rows) == 2  # both members are still stored for audit
        assert rows[0].result is None  # owner: dispatched later by the drain loop
        duplicate = json.loads(rows[1].result)
        assert duplicate["status"] == dedupe.DUPLICATE_STATUS
        assert duplicate["dispatch_owner_space_event_id"] == "63"

        groups = _groups(factory)
        assert len(groups) == 1
        assert groups[0].dedupe_key == INCIDENT_DEDUPE_KEY
        assert groups[0].status == dedupe.GROUP_STATUS_PENDING


def test_two_distinct_messages_still_route_to_two_dispatches(tmp_path):
    """AC5: no regression for genuinely different user messages."""
    second = _message_payload(900, "message_created")
    second["group_id"] = "a07b309c-5a57-4c63-ba45-383390713384"
    second["event_id"] = 32
    second["event_data"]["content_payload"]["message_id"] = 32
    second["event_data"]["content_payload"]["text"] = "and a second question"
    second["event_data"]["content"] = "and a second question"

    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)
        _post(client, INCIDENT_AI_QUESTION_ASKED)
        _post(client, second)

        assert [item.space_event_id for item in queued] == ["63", "900"]
        assert len({item.dedupe_key for item in queued}) == 2
        assert len(_groups(factory)) == 2


def test_redelivered_and_sibling_account_events(tmp_path):
    """Only a byte-identical redelivery is dropped; the sibling event still routes."""
    settings = _account_event(65, "account_settings_updated", group_id="c5c19ed2-group", occurred_at="2026-09-16T03:12:13Z")
    access = _account_event(
        66,
        "account_bot_access_updated",
        group_id="c5c19ed2-group",
        occurred_at="2026-09-16T03:12:13Z",
        allowed_bot_user_ids=[2, 4],
    )

    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, settings)
        _post(client, settings)  # redelivery of the same Rails event
        _post(client, access)  # a different fact in the same group

        assert [item.space_event_id for item in queued] == ["65", "66"]
        rows = _rows(factory)
        assert len(rows) == 3
        assert json.loads(rows[1].result)["status"] == dedupe.DUPLICATE_STATUS


def test_duplicate_is_never_queued_even_after_the_owner_was_dispatched(tmp_path):
    """AC3: a late member of a dispatched group cannot re-route it."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)

        db = factory()
        try:
            group = db.query(SpaceEventDispatchGroup).one()
            group.status = dedupe.GROUP_STATUS_DISPATCHED
            db.commit()
        finally:
            db.close()

        _post(client, INCIDENT_AI_QUESTION_ASKED)

        assert [item.space_event_id for item in queued] == ["63"]


# ---------------------------------------------------------------- drain (AC1/AC3/AC4)


def test_drain_dispatches_one_merged_call_and_marks_both_members(tmp_path):
    """The single dispatch carries the bot addressing and closes both member rows."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)
        _post(client, INCIDENT_AI_QUESTION_ASKED)
        item = queued[0]

        hermes = AsyncMock(return_value={"id": "chatcmpl-test", "object": "chat.completion"})

        with (
            patch("bus.executors._send_to_hermes", hermes),
            patch("bus.executors.SPACE_EVENT_FIRE_AND_FORGET", False),
            patch("bus.executors.SPACE_EVENT_MERGE_SETTLE_SECONDS", 0),
        ):
            import asyncio

            response = asyncio.run(_run_drain(item))

    assert response == {"id": "chatcmpl-test", "object": "chat.completion"}
    assert hermes.await_count == 1  # exactly one dispatch artifact for the pair

    payload = hermes.await_args.args[0]
    content = payload["messages"][0]["content"]
    assert "ai_question_asked" in content
    assert '"bot_user_ids": [7]' in content
    assert "what about business canvas?" in content

    rows = _rows(factory)
    assert all(row.sent_date is not None for row in rows)  # both marked handled together
    assert json.loads(rows[0].result)["id"] == "chatcmpl-test"
    assert json.loads(rows[1].result)["status"] == dedupe.DUPLICATE_STATUS

    group = _groups(factory)[0]
    assert group.status == dedupe.GROUP_STATUS_DISPATCHED
    assert group.dispatched_at is not None


async def _run_drain(item):
    from bus.executors import run_space_event

    return await run_space_event(item)


def test_drain_failure_marks_every_member(tmp_path):
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)
        _post(client, INCIDENT_AI_QUESTION_ASKED)
        item = queued[0]

        failing = AsyncMock(side_effect=RuntimeError("hermes down"))

        with (
            patch("bus.executors._send_to_hermes", failing),
            patch("bus.executors.SPACE_EVENT_FIRE_AND_FORGET", False),
            patch("bus.executors.SPACE_EVENT_MERGE_SETTLE_SECONDS", 0),
        ):
            import asyncio

            assert asyncio.run(_run_drain(item)) is None

    rows = _rows(factory)
    assert len(rows) == 2
    assert all(json.loads(row.result)["status"] == "error" for row in rows)
    assert _groups(factory)[0].status == dedupe.GROUP_STATUS_FAILED


# ---------------------------------------------------------------- settle window


def test_group_settles_before_the_merge_window_closes(tmp_path):
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue():
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)

        db = factory()
        try:
            assert dedupe.group_is_settling(db, INCIDENT_DEDUPE_KEY, settle_seconds=3) is True

            group = db.query(SpaceEventDispatchGroup).one()
            group.created_at = datetime.now(timezone.utc) - timedelta(seconds=30)
            db.commit()

            assert dedupe.group_is_settling(db, INCIDENT_DEDUPE_KEY, settle_seconds=3) is False
            assert dedupe.group_is_settling(db, INCIDENT_DEDUPE_KEY, settle_seconds=0) is False
            assert dedupe.group_is_settling(db, None, settle_seconds=3) is False
        finally:
            db.close()


def test_settling_item_is_requeued_instead_of_dispatched(tmp_path):
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)
        item = queued[0]

        hermes = AsyncMock(return_value={"id": "should-not-be-called"})

        with (
            patch("bus.executors._send_to_hermes", hermes),
            patch("bus.executors.SPACE_EVENT_FIRE_AND_FORGET", False),
            patch("bus.executors.SPACE_EVENT_MERGE_SETTLE_SECONDS", 60),
        ):
            import asyncio

            result = asyncio.run(_run_drain(item))

            assert result["status"] == "deferred_merge_window"
            assert hermes.await_count == 0
            assert space_events_queue.qsize() == 1  # put back for the next tick
            while not space_events_queue.empty():
                space_events_queue.get_nowait()
                space_events_queue.task_done()


# ---------------------------------------------------------------- restart recovery


def test_recovery_requeues_un_dispatched_claims_and_rows(tmp_path):
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)
        _post(client, INCIDENT_AI_QUESTION_ASKED)  # duplicate member: never recovered

        recovered = dedupe.pending_dispatch_items(max_age_seconds=900)

    assert [item.space_event_id for item in recovered] == ["63"]
    assert recovered[0].dedupe_key == INCIDENT_DEDUPE_KEY

    rows = _rows(factory)
    assert len(rows) == 2
    assert json.loads(rows[1].result)["status"] == dedupe.DUPLICATE_STATUS


def test_recovery_stamps_a_merged_duplicate_once_its_unit_was_dispatched(tmp_path):
    """The msg-36 residual loop: a merged twin is handled, never reported as pending."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)
        _post(client, INCIDENT_AI_QUESTION_ASKED)
        item = queued[0]
        hermes = AsyncMock(return_value={"id": "chatcmpl-1"})

        with (
            patch("bus.executors._send_to_hermes", hermes),
            patch("bus.executors.SPACE_EVENT_FIRE_AND_FORGET", False),
            patch("bus.executors.SPACE_EVENT_MERGE_SETTLE_SECONDS", 0),
        ):
            import asyncio

            asyncio.run(_run_drain(item))

        # simulate a duplicate row that predates the stamp: result set, sent_date empty
        db = factory()
        try:
            duplicate = db.query(SpaceEvent).order_by(SpaceEvent.id).all()[1]
            duplicate.sent_date = None
            db.commit()
        finally:
            db.close()

        assert dedupe.pending_dispatch_items(max_age_seconds=900) == []
        rows = _rows(factory)
        assert rows[1].sent_date is not None


def test_recovery_skips_dispatched_groups_and_failed_rows(tmp_path):
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue():
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)
        _post(client, INCIDENT_AI_QUESTION_ASKED)

        db = factory()
        try:
            group = db.query(SpaceEventDispatchGroup).one()
            group.status = dedupe.GROUP_STATUS_DISPATCHED
            rows = db.query(SpaceEvent).order_by(SpaceEvent.id).all()
            for row in rows:
                row.sent_date = datetime.now(timezone.utc)
            error_row = SpaceEvent(
                space_event_id="9001",
                event_type="project_member_added",
                event_data={"room_id": None},
                result=json.dumps({"status": "error", "error_type": "HTTPStatusError"}),
            )
            db.add(error_row)
            db.commit()

            assert dedupe.pending_dispatch_items(max_age_seconds=900) == []
        finally:
            db.close()


def test_recovery_window_excludes_old_rows(tmp_path):
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue():
        client = TestClient(app)
        _post(client, INCIDENT_MESSAGE_CREATED)

        assert dedupe.pending_dispatch_items(max_age_seconds=0) == []


def _seed_legacy_rows(factory, *, first_dispatched=False):
    """Store the incident pair the way the pre-dedupe bridge did: no dedupe_key."""
    db = factory()
    try:
        created = SpaceEvent(
            space_event_id="81",
            event_type="message_created",
            event_id=str(MESSAGE_ID),
            group_id=GROUP_ID,
            event_data=INCIDENT_MESSAGE_CREATED["event_data"],
            created_at="2026-09-16T03:16:53Z",
            dedupe_key=None,
            sent_date=datetime.now(timezone.utc) if first_dispatched else None,
        )
        asked = SpaceEvent(
            space_event_id="82",
            event_type="ai_question_asked",
            event_id=str(MESSAGE_ID),
            group_id=GROUP_ID,
            event_data=INCIDENT_AI_QUESTION_ASKED["event_data"],
            created_at="2026-09-16T03:16:53Z",
            dedupe_key=None,
        )
        db.add_all([created, asked])
        db.commit()
        return created.id, asked.id
    finally:
        db.close()


def test_legacy_pair_is_recovered_as_one_dispatch(tmp_path):
    """Rows stored before the feature are attached to their unit and merged."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue():
        created_id, asked_id = _seed_legacy_rows(factory)

        recovered = dedupe.pending_dispatch_items(max_age_seconds=900)

        assert [item.space_event_id for item in recovered] == ["81"]
        assert recovered[0].dedupe_key == INCIDENT_DEDUPE_KEY

        rows = {row.id: row for row in _rows(factory)}
        assert rows[created_id].dedupe_key == INCIDENT_DEDUPE_KEY
        assert rows[asked_id].dedupe_key == INCIDENT_DEDUPE_KEY  # backfilled as well
        assert json.loads(rows[asked_id].result)["status"] == dedupe.DUPLICATE_STATUS


def test_recovery_does_not_requeue_a_dispatched_legacy_unit(tmp_path):
    """The msg-36 defect: a twin of an already dispatched message must never be re-sent."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue():
        created_id, asked_id = _seed_legacy_rows(factory, first_dispatched=True)

        assert dedupe.pending_dispatch_items(max_age_seconds=900) == []

        rows = {row.id: row for row in _rows(factory)}
        duplicate = json.loads(rows[asked_id].result)
        assert duplicate["status"] == dedupe.DUPLICATE_STATUS
        assert duplicate["dispatch_owner_row_id"] == created_id


def test_drain_skips_twin_of_an_already_dispatched_legacy_unit(tmp_path):
    """A twin already sitting in the queue is dropped at drain time, not re-routed."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue():
        _seed_legacy_rows(factory, first_dispatched=True)
        twin = SpaceEventQueueItem(
            space_event_id="82",
            event_type="ai_question_asked",
            event_data=INCIDENT_AI_QUESTION_ASKED["event_data"],
            dedupe_key=None,
        )
        hermes = AsyncMock(return_value={"id": "must-not-be-called"})

        with (
            patch("bus.executors._send_to_hermes", hermes),
            patch("bus.executors.SPACE_EVENT_FIRE_AND_FORGET", False),
            patch("bus.executors.SPACE_EVENT_MERGE_SETTLE_SECONDS", 0),
        ):
            import asyncio

            result = asyncio.run(_run_drain(twin))

        assert result["status"] == "skipped_already_dispatched"
        assert hermes.await_count == 0

        rows = _rows(factory)
        asked = next(row for row in rows if row.space_event_id == "82")
        assert json.loads(asked.result)["status"] == dedupe.DUPLICATE_STATUS
        # handled: the member was carried by the unit's single dispatch, and a row with a
        # result is never re-queued by the restart recovery again
        assert asked.sent_date is not None


def test_drain_resolves_the_queued_row_when_the_rails_event_id_is_replayed(tmp_path):
    """A replayed webhook keeps its Rails event id; the queued ROW must still win.

    Regression for the live replay: resolving the item by space_event_id picked the
    historical row of the same id and attributed the response to it.
    """
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue() as queued:
        client = TestClient(app)

        db = factory()
        try:
            db.add(
                SpaceEvent(
                    space_event_id="63",  # same Rails event id as INCIDENT_MESSAGE_CREATED
                    event_type="message_created",
                    event_id=str(MESSAGE_ID),
                    group_id=GROUP_ID,
                    event_data=INCIDENT_MESSAGE_CREATED["event_data"],
                    created_at="2026-09-16T03:03:03Z",
                    sent_date=datetime.now(timezone.utc) - timedelta(hours=3),
                    result=json.dumps({"id": "historical"}),
                )
            )
            db.commit()
            historical_id = db.query(SpaceEvent).one().id
        finally:
            db.close()

        _post(client, INCIDENT_MESSAGE_CREATED)
        _post(client, INCIDENT_AI_QUESTION_ASKED)
        item = queued[0]
        assert item.space_event_row_id is not None
        assert item.space_event_row_id != historical_id

        hermes = AsyncMock(return_value={"id": "chatcmpl-replay"})
        with (
            patch("bus.executors._send_to_hermes", hermes),
            patch("bus.executors.SPACE_EVENT_FIRE_AND_FORGET", False),
            patch("bus.executors.SPACE_EVENT_MERGE_SETTLE_SECONDS", 0),
        ):
            import asyncio

            asyncio.run(_run_drain(item))

        rows = {row.id: row for row in _rows(factory)}
        assert json.loads(rows[historical_id].result)["id"] == "historical"
        assert json.loads(rows[item.space_event_row_id].result)["id"] == "chatcmpl-replay"


def test_legacy_guard_is_windowed_to_the_replay_window(tmp_path):
    """A pair explicitly re-sent after the window is new work, not a stale twin."""
    with _isolated_bridge_db(tmp_path) as factory, _record_dispatch_queue():
        created_id, asked_id = _seed_legacy_rows(factory, first_dispatched=True)

        db = factory()
        try:
            row = db.get(SpaceEvent, created_id)
            row.sent_date = datetime.now(timezone.utc) - timedelta(hours=3)
            db.commit()
        finally:
            db.close()

        twin = SpaceEventQueueItem(
            space_event_id="82",
            event_type="ai_question_asked",
            event_data=INCIDENT_AI_QUESTION_ASKED["event_data"],
            dedupe_key=None,
        )
        hermes = AsyncMock(return_value={"id": "chatcmpl-replayed"})

        with (
            patch("bus.executors._send_to_hermes", hermes),
            patch("bus.executors.SPACE_EVENT_FIRE_AND_FORGET", False),
            patch("bus.executors.SPACE_EVENT_MERGE_SETTLE_SECONDS", 0),
        ):
            import asyncio

            assert asyncio.run(_run_drain(twin)) == {"id": "chatcmpl-replayed"}

        assert hermes.await_count == 1
        assert dedupe.pending_dispatch_items(max_age_seconds=900) == []

