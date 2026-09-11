from sqlalchemy import inspect

from db.database import Base
from db.models import ApiException, Bot, McpCallLog, McpException, SpaceEvent


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


def test_mcp_exception_model_exposes_expected_columns_and_table_name():
    mapper = inspect(McpException)

    assert mapper.primary_key[0].name == "id"
    assert mapper.mapped_table.name == "mcp_exceptions"
    assert "tool_call_name" in mapper.columns
    assert "exception" in mapper.columns
    assert "stored_exception" in mapper.columns
    assert "created_at" in mapper.columns


def test_api_exception_model_exposes_expected_columns_and_table_name():
    mapper = inspect(ApiException)

    assert mapper.primary_key[0].name == "id"
    assert mapper.mapped_table.name == "api_exceptions"
    assert "service_name" in mapper.columns
    assert "method" in mapper.columns
    assert "endpoint" in mapper.columns
    assert "status_code" in mapper.columns
    assert "error_type" in mapper.columns
    assert "error_message" in mapper.columns
    assert "stored_exception" in mapper.columns
    assert "request_context" in mapper.columns
    assert "created_at" in mapper.columns


def test_mcp_call_log_model_exposes_expected_columns_and_table_name():
    mapper = inspect(McpCallLog)

    assert mapper.primary_key[0].name == "id"
    assert mapper.mapped_table.name == "mcp_call_logs"
    assert "jsonrpc_id" in mapper.columns
    assert "tool_call_name" in mapper.columns
    assert "params_sanitized" in mapper.columns
    assert "is_error" in mapper.columns
    assert "error_message" in mapper.columns
    assert "result_preview" in mapper.columns
    assert "result_size" in mapper.columns
    assert "duration_ms" in mapper.columns
    assert "created_at" in mapper.columns


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
