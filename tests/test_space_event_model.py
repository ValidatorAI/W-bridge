from sqlalchemy import inspect

from db.models import SpaceEvent


def test_space_event_model_has_internal_primary_key_and_json_field():
    mapper = inspect(SpaceEvent)

    assert mapper.primary_key[0].name == "id"
    assert "space_event_id" in mapper.columns
    assert mapper.columns["event_data"].type.__class__.__name__ == "JSON"
    assert "stored_date" in mapper.columns
    assert "sent_date" in mapper.columns
    assert "result" in mapper.columns
