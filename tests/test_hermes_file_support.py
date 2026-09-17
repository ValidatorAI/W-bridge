import asyncio
from unittest.mock import AsyncMock, patch

from agent.hermes import chat_completions, files_download
from bus.executors import _extract_event_attachments, _run_space_event_and_update
from bus.queues import SpaceEventQueueItem
from db.models import SpaceEvent


def test_chat_completions_uses_multipart_when_files_are_present():
    async_request = AsyncMock(return_value={"ok": True})
    payload = {"messages": [{"role": "user", "content": "hello"}]}
    files = {"file_1": ("notes.txt", b"abc", "text/plain")}

    with patch("agent.hermes._request", async_request):
        result = asyncio.run(chat_completions(payload, files=files, profile="delegator"))

    assert result == {"ok": True}
    kwargs = async_request.await_args.kwargs
    assert kwargs.get("json") is None
    assert kwargs["files"] == files
    assert "payload" in kwargs["data"]


def test_files_download_delegates_to_request_bytes():
    async_request_bytes = AsyncMock(return_value=(b"file-bytes", {"content-type": "application/pdf"}))

    with patch("agent.hermes._request_bytes", async_request_bytes):
        payload, headers = asyncio.run(files_download("file_123", profile="delegator"))

    assert payload == b"file-bytes"
    assert headers["content-type"] == "application/pdf"
    kwargs = async_request_bytes.await_args.kwargs
    assert kwargs["profile"] == "delegator"


def test_extract_event_attachments_supports_url_and_message_attachment_shapes():
    event_data = {
        "message": {
            "id": 77,
            "room_id": 12,
            "project_id": 6,
            "has_attachment": True,
            "attachment_filename": "spec.pdf",
            "attachment_content_type": "application/pdf",
            "attachment_url": "https://example.com/spec.pdf",
        },
        "nested": {
            "files": [
                {
                    "name": "image.png",
                    "mime_type": "image/png",
                    "url": "https://example.com/image.png",
                }
            ]
        },
    }

    attachments = _extract_event_attachments(event_data)

    assert len(attachments) == 2
    assert attachments[0]["message_id"] == "77"
    assert attachments[0]["room_id"] == "12"
    assert attachments[0]["project_id"] == "6"
    assert attachments[0]["url"] == "https://example.com/spec.pdf"


def test_run_space_event_appends_attachment_references_when_upload_unavailable():
    class _FakeDb:
        def __init__(self) -> None:
            self.commits = 0
            self.rollbacks = 0

        def commit(self) -> None:
            self.commits += 1

        def rollback(self) -> None:
            self.rollbacks += 1

    db = _FakeDb()
    space_event = SpaceEvent(id=1)
    item = SpaceEventQueueItem(
        space_event_id="evt-1",
        event_type="message.created",
        event_data={
            "message": {
                "id": 10,
                "room_id": 20,
                "has_attachment": True,
                "attachment_filename": "artifact.zip",
                "attachment_content_type": "application/zip",
                "attachment_url": "https://example.com/artifact.zip",
            }
        },
        profile="delegator",
    )

    send_mock = AsyncMock(return_value={"status": "ok"})
    with (
        patch("bus.executors._send_to_hermes", send_mock),
        patch("bus.executors.HERMES_EVENT_FILE_UPLOAD_ENABLED", False),
        patch("bus.executors.HERMES_EVENT_FILE_URL_FALLBACK", True),
    ):
        response = asyncio.run(_run_space_event_and_update(item, space_event, db))

    assert response == {"status": "ok"}
    payload = send_mock.await_args.args[0]
    content = payload["messages"][0]["content"]
    assert "Attachments:" in content
    assert "artifact.zip" in content
    assert db.commits == 1
    assert db.rollbacks == 0
