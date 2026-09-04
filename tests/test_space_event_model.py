from sqlalchemy import inspect

from db.database import Base
from db.models import Bot, SpaceEvent


def test_bot_model_has_no_token_column():
    mapper = inspect(Bot)

    assert mapper.primary_key[0].name == "id"
    assert "name" in mapper.columns
    assert "profile_name" in mapper.columns
    assert "active" in mapper.columns
    assert "token" not in mapper.columns


def test_space_event_model_has_internal_primary_key_and_json_field():
    mapper = inspect(SpaceEvent)

    assert mapper.primary_key[0].name == "id"
    assert "space_event_id" in mapper.columns
    assert mapper.columns["event_data"].type.__class__.__name__ == "JSON"
    assert "stored_date" in mapper.columns
    assert "sent_date" in mapper.columns
    assert "result" in mapper.columns


def test_legacy_session_tracking_tables_are_removed_from_orm_metadata():
    table_names = {table.name for table in Base.metadata.tables.values()}

    assert "sessions" not in table_names
    assert "room_pointers" not in table_names
    assert "message_sessions" not in table_names
    assert "reply_sessions" not in table_names
    assert "hermes_sessions" not in table_names
    assert "hermess_messages" not in table_names
    assert "message_logs" not in table_names
    assert "bot_replies" not in table_names
