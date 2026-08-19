from pydantic import BaseModel, ConfigDict, Field


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class WebhookQueryParams(SchemaModel):
    token: str | None = None
    selected_profile: str | None = Field(default=None, alias="selected_profile")
    profile: str | None = None
    bot: str | None = None


class WebhookResponse(SchemaModel):
    message: str = ""
