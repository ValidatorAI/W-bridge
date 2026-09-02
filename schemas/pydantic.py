from pydantic import BaseModel, ConfigDict, Field
from typing import Any


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class WebhookQueryParams(SchemaModel):
    token: str | None = None
    selected_profile: str | None = Field(default=None, alias="selected_profile")
    profile: str | None = None
    bot: str | None = None


class WebhookResponse(SchemaModel):
    message: str = ""


class ChatCompletionsInput(SchemaModel):
    payload: dict[str, Any]
    session_id: str | None = None
    session_key: str | None = None
    profile: str | None = None


class SendChatHistoryInput(SchemaModel):
    history: list[dict[str, Any]] = Field(default_factory=list)
    session_id: str | None = None
    profile: str | None = None


class SpaceEventInput(SchemaModel):
    id: int | str | None = None
    event_type: str | None = None
    event_id: str | None = None
    group_id: str | None = None
    event_data: dict[str, Any] | None = None
    created_at: str | None = None
