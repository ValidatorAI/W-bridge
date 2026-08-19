from typing import Any, TypedDict


class AttachmentPart(TypedDict, total=False):
    type: str
    text: str
    file_url: str
    mime_type: str
    filename: str


class HermesMessage(TypedDict):
    role: str
    content: str | list[AttachmentPart]


class HermesSessionPayload(TypedDict, total=False):
    id: str
    session_id: str
    session: dict[str, Any]
    data: dict[str, Any]
