from pydantic import BaseModel, ConfigDict, Field
from typing import Any


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SpaceEventInput(SchemaModel):
    id: int | str | None = None
    event_type: str | None = None
    event_id: int | str | None = None
    group_id: str | None = None
    event_data: dict[str, Any] | None = None
    created_at: str | None = None
