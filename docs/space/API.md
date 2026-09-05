# `space.api` — Async Bonfire API Client

Thin async Python wrapper around the Bonfire HTTP API described in
[API_REFERENCE.md](../hermes/API_REFERENCE.md). One `async def` per endpoint, 100 in total,
all re-exported flat from the `space.api` package.

Source: [space/api/](../../space/api/)

## Configuration

Read from the environment via [hermpers/environment.py](../../hermpers/environment.py):

| Variable | Default | Purpose |
|---|---|---|
| `OUTPUT_BASE_URL` | `http://localhost:3000` | Bonfire server root; `/api` is appended automatically |
| `OUTPUT_EVENTS_TOKEN` | `""` | Sent as `Authorization: Bearer <token>` on every request |
| `OUTPUT_HTTP_TIMEOUT` | `60` | Per-request timeout in seconds |

## Usage

```python
from space import api

projects = await api.list_projects()
rooms = await api.list_rooms(projects[0]["id"])
await api.create_message(project_id, room_id, user_id, body="hello")

await api.aclose_client()  # on application shutdown
```

## Conventions

- **All functions are `async`.** Every call must be awaited.
- **Returns** the parsed JSON body — a `dict` or `list`. `DELETE` endpoints return `204 No Content`
  and therefore return `None`. Attachment downloads return raw `bytes`.
- **Errors are raised, not swallowed.** `response.raise_for_status()` means a non-2xx response
  raises `httpx.HTTPStatusError`; connection failures raise `httpx.RequestError`.
- **Optional arguments are keyword-only** and default to `None`. Any argument left as `None` is
  omitted from the request entirely, so the server's own defaults apply.
- **Positional arguments** are the path segments plus the endpoint's required body fields.
- **Pagination**: list endpoints accept `page` and `per_page` (server default 40, max 200). Omitting
  `page` on message lists returns the full unpaginated list.
- **Connection reuse**: a single lazily-created `httpx.AsyncClient` is shared by all calls. Call
  `aclose_client()` at shutdown to release it; the next call transparently recreates it.

### File uploads

Parameters typed `FileUpload` accept an httpx file tuple — `(filename, content, content_type)`,
where `content` is `bytes` or an open binary file object. The `content_type` element is optional:

```python
with open("diagram.png", "rb") as fp:
    await api.create_message(1, 2, 5, attachment=("diagram.png", fp, "image/png"))
```

When a file is supplied, the request is sent as `multipart/form-data`; otherwise it is sent as JSON.

---

## Projects

| Function | Endpoint |
|---|---|
| `list_projects` | `GET /api/projects` |
| `get_project` | `GET /api/projects/:id` |

```python
async def list_projects() -> list[dict[str, Any]]
async def get_project(project: int | str) -> dict[str, Any]
```

`project` accepts either the numeric id or the project slug.

---

## Rooms

| Function | Endpoint |
|---|---|
| `list_rooms` | `GET /api/projects/:project_id/rooms` |
| `get_room` | `GET /api/projects/:project_id/rooms/:id` |
| `list_room_threads` | `GET /api/projects/:project_id/rooms/:id/threads` |
| `search_rooms` | `GET /api/projects/:project_id/rooms/search?q=` |

```python
async def list_rooms(project_id: int | str) -> list[dict[str, Any]]
async def get_room(project_id: int | str, room_id: int | str) -> dict[str, Any]
async def list_room_threads(project_id: int | str, room_id: int | str) -> list[dict[str, Any]]
async def search_rooms(project_id: int | str, q: str) -> list[dict[str, Any]]
```

`list_room_threads` returns the room's child rooms. `search_rooms` is a fuzzy, case-insensitive
name search ranked by relevance.

---

## Messages

Nested routes plus the flat `/api/messages/:id` equivalents (message ids are globally unique).
Create/update/delete broadcast realtime Turbo Stream updates to connected web clients.

| Function | Endpoint |
|---|---|
| `list_messages` | `GET /api/projects/:project_id/rooms/:room_id/messages` |
| `create_message` | `POST /api/projects/:project_id/rooms/:room_id/messages` |
| `get_message` | `GET /api/projects/:project_id/rooms/:room_id/messages/:id` |
| `update_message` | `PATCH /api/projects/:project_id/rooms/:room_id/messages/:id` |
| `delete_message` | `DELETE /api/projects/:project_id/rooms/:room_id/messages/:id` |
| `download_message_attachment` | `GET /api/projects/:project_id/rooms/:room_id/messages/:id/attachment` |
| `get_message_by_id` | `GET /api/messages/:id` |
| `update_message_by_id` | `PATCH /api/messages/:id` |
| `delete_message_by_id` | `DELETE /api/messages/:id` |
| `download_attachment_by_id` | `GET /api/messages/:id/attachment` |

```python
async def list_messages(
    project_id: int | str,
    room_id: int | str,
    *,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def create_message(
    project_id: int | str,
    room_id: int | str,
    user_id: int | str,
    *,
    body: str | None = None,
    attachment: FileUpload | None = None,
) -> dict[str, Any]

async def get_message(
    project_id: int | str, room_id: int | str, message_id: int | str
) -> dict[str, Any]

async def update_message(
    project_id: int | str,
    room_id: int | str,
    message_id: int | str,
    *,
    body: str | None = None,
    attachment: FileUpload | None = None,
) -> dict[str, Any]

async def delete_message(
    project_id: int | str, room_id: int | str, message_id: int | str
) -> None

async def download_message_attachment(
    project_id: int | str,
    room_id: int | str,
    message_id: int | str,
    *,
    disposition: str | None = None,
) -> bytes

async def get_message_by_id(message_id: int | str) -> dict[str, Any]

async def update_message_by_id(
    message_id: int | str,
    *,
    body: str | None = None,
    attachment: FileUpload | None = None,
) -> dict[str, Any]

async def delete_message_by_id(message_id: int | str) -> None

async def download_attachment_by_id(
    message_id: int | str, *, disposition: str | None = None
) -> bytes
```

- `create_message` / `update_message` require at least one of `body` or `attachment`.
- `disposition="attachment"` forces a download instead of inline display.

---

## Actions

| Function | Endpoint |
|---|---|
| `send_action` | `POST /api/projects/:project_id/rooms/:room_id/actions` |

```python
async def send_action(
    project_id: int | str,
    room_id: int | str,
    user_id: int | str,
    action_type: str,
) -> dict[str, Any]
```

`action_type` is `typing_start` or `typing_stop`. The parameter is deliberately named `action_type`
because `action` is reserved by Rails routing. This endpoint only broadcasts; nothing is persisted.

---

## Decisions

| Function | Endpoint |
|---|---|
| `create_decision` | `POST /api/projects/:project_id/rooms/:room_id/decisions` |

```python
async def create_decision(
    project_id: int | str,
    room_id: int | str,
    user_id: int | str,
    approval_request_id: int | str,
    decision: str,
    *,
    note: str | None = None,
) -> dict[str, Any]
```

`decision` is one of `approve`, `confirm`, `deny`, `cancel`. The approval request must belong to the
given room.

---

## Attention Items

| Function | Endpoint |
|---|---|
| `list_attention_items` | `GET /api/attention_items` |
| `get_attention_item` | `GET /api/attention_items/:id` |
| `create_attention_item` | `POST /api/attention_items` |
| `update_attention_item` | `PATCH /api/attention_items/:id` |
| `delete_attention_item` | `DELETE /api/attention_items/:id` |

```python
async def list_attention_items(
    *,
    id: int | str | None = None,
    category: str | None = None,
    title: str | None = None,
    meta_text: str | None = None,
    due_at: str | None = None,
    overdue: bool | None = None,
    status: str | None = None,
    project_id: int | str | None = None,
    room_id: int | str | None = None,
    user_id: int | str | None = None,
    source_id: int | str | None = None,
    source_type: str | None = None,
    target_id: int | str | None = None,
    target_type: str | None = None,
    action_label: str | None = None,
    ai_confirm: bool | None = None,
    created_at_gt: str | None = None,
    created_at_lt: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_attention_item(attention_item_id: int | str) -> dict[str, Any]

async def create_attention_item(
    title: str,
    category: str,
    *,
    meta_text: str | None = None,
    due_at: str | None = None,
    status: str | None = None,
    overdue: bool | None = None,
    project_id: int | str | None = None,
    room_id: int | str | None = None,
    user_id: int | str | None = None,
    source_id: int | str | None = None,
    source_type: str | None = None,
    target_id: int | str | None = None,
    target_type: str | None = None,
    action_label: str | None = None,
    ai_confirm: bool | None = None,
) -> dict[str, Any]

async def update_attention_item(
    attention_item_id: int | str, *, <same optional fields as create, plus title/category>
) -> dict[str, Any]

async def delete_attention_item(attention_item_id: int | str) -> None
```

`created_at_gt` / `created_at_lt` bound the creation date range.

---

## Company Status Periods

| Function | Endpoint |
|---|---|
| `list_company_status_periods` | `GET /api/company_status_periods` |
| `get_company_status_period` | `GET /api/company_status_periods/:id` |
| `get_current_company_status_period` | `GET /api/company_status_periods/current` |
| `get_company_status_period_by_slug` | `GET /api/company_status_periods/by_slug/:slug` |
| `get_company_status_period_by_name` | `GET /api/company_status_periods/by_name?name=` |
| `create_company_status_period` | `POST /api/company_status_periods` |
| `update_company_status_period` | `PATCH /api/company_status_periods/:id` |
| `delete_company_status_period` | `DELETE /api/company_status_periods/:id` |

```python
async def list_company_status_periods() -> dict[str, Any]
async def get_company_status_period(period_id: int | str) -> dict[str, Any]
async def get_current_company_status_period() -> dict[str, Any]
async def get_company_status_period_by_slug(slug: str) -> dict[str, Any]
async def get_company_status_period_by_name(name: str) -> dict[str, Any]

async def create_company_status_period(
    name: str,
    *,
    slug: str | None = None,
    current: bool | None = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_company_status_period(
    period_id: int | str,
    *,
    name: str | None = None,
    slug: str | None = None,
    current: bool | None = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def delete_company_status_period(period_id: int | str) -> None
```

`slug` is auto-generated from `name` when omitted. Name lookup is case-insensitive.

---

## Company Status Items

| Function | Endpoint |
|---|---|
| `list_company_status_items` | `GET /api/company_status_items` |
| `get_company_status_item` | `GET /api/company_status_items/:id` |
| `list_company_status_items_by_period` | `GET /api/company_status_items/by_period` |
| `filter_company_status_items` | `GET /api/company_status_items/advanced_filter` |
| `create_company_status_item` | `POST /api/company_status_items` |
| `update_company_status_item` | `PATCH /api/company_status_items/:id` |
| `delete_company_status_item` | `DELETE /api/company_status_items/:id` |

```python
async def list_company_status_items(
    *,
    company_status_period_id: int | str | None = None,
    project_id: int | str | None = None,
    category: str | None = None,
    status: str | None = None,
    health: str | None = None,
    badge: str | None = None,
    owner_name: str | None = None,
    source_type: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_company_status_item(item_id: int | str) -> dict[str, Any]

async def list_company_status_items_by_period(
    company_status_period_id: int | str,
) -> dict[str, Any]

async def filter_company_status_items(
    *,  # same filters as list_company_status_items, plus:
    created_at_gt: str | None = None,
    created_at_lt: str | None = None,
) -> dict[str, Any]

async def create_company_status_item(
    company_status_period_id: int | str,
    title: str,
    category: str,
    *,
    status: str | None = None,
    health: str | None = None,
    badge: str | None = None,
    summary: str | None = None,
    details: str | None = None,
    owner_name: str | None = None,
    position: int | None = None,
    project_id: int | str | None = None,
) -> dict[str, Any]

async def update_company_status_item(
    item_id: int | str, *, <same optional fields as create>
) -> dict[str, Any]

async def delete_company_status_item(item_id: int | str) -> None
```

---

## Project Users

| Function | Endpoint |
|---|---|
| `list_project_users` | `GET /api/projects/:project_id/users` |
| `get_project_user` | `GET /api/projects/:project_id/users/:id` |

```python
async def list_project_users(
    project_id: int | str, *, page: int | None = None, per_page: int | None = None
) -> dict[str, Any]

async def get_project_user(project_id: int | str, user_id: int | str) -> dict[str, Any]
```

---

## Project All-Hands

Three parallel resources — takeaways, decisions, and action items — each with the same five CRUD
operations. All list functions accept `active`, `page`, and `per_page`.

| Function | Endpoint |
|---|---|
| `list_all_hands_takeaways` | `GET /api/projects/:project_id/project_all_hands_takeaways` |
| `get_all_hands_takeaway` | `GET .../project_all_hands_takeaways/:id` |
| `create_all_hands_takeaway` | `POST .../project_all_hands_takeaways` |
| `update_all_hands_takeaway` | `PATCH .../project_all_hands_takeaways/:id` |
| `delete_all_hands_takeaway` | `DELETE .../project_all_hands_takeaways/:id` |
| `list_all_hands_decisions` | `GET /api/projects/:project_id/project_all_hands_decisions` |
| `get_all_hands_decision` | `GET .../project_all_hands_decisions/:id` |
| `create_all_hands_decision` | `POST .../project_all_hands_decisions` |
| `update_all_hands_decision` | `PATCH .../project_all_hands_decisions/:id` |
| `delete_all_hands_decision` | `DELETE .../project_all_hands_decisions/:id` |
| `list_all_hands_action_items` | `GET /api/projects/:project_id/project_all_hands_action_items` |
| `get_all_hands_action_item` | `GET .../project_all_hands_action_items/:id` |
| `create_all_hands_action_item` | `POST .../project_all_hands_action_items` |
| `update_all_hands_action_item` | `PATCH .../project_all_hands_action_items/:id` |
| `delete_all_hands_action_item` | `DELETE .../project_all_hands_action_items/:id` |

```python
async def list_all_hands_takeaways(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_all_hands_takeaway(
    project_id: int | str, takeaway_id: int | str
) -> dict[str, Any]

async def create_all_hands_takeaway(
    project_id: int | str,
    category: str,
    content: str,
    *,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_all_hands_takeaway(
    project_id: int | str,
    takeaway_id: int | str,
    *,
    category: str | None = None,
    content: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def delete_all_hands_takeaway(project_id: int | str, takeaway_id: int | str) -> None

async def create_all_hands_decision(
    project_id: int | str,
    title: str,
    *,
    basis: str | None = None,
    impact: str | None = None,
    badge: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_all_hands_decision(
    project_id: int | str, decision_id: int | str, *, title: str | None = None, ...
) -> dict[str, Any]

async def create_all_hands_action_item(
    project_id: int | str,
    title: str,
    *,
    assignee_name: str | None = None,
    due_date: str | None = None,
    completed: bool | None = None,
    completed_at: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_all_hands_action_item(
    project_id: int | str, action_item_id: int | str, *, title: str | None = None, ...
) -> dict[str, Any]
```

The `get_*` and `delete_*` functions for decisions and action items mirror the takeaway versions,
taking `(project_id, decision_id)` and `(project_id, action_item_id)` respectively.

---

## Knowledge Items

| Function | Endpoint |
|---|---|
| `list_knowledge_items` | `GET /api/projects/:project_id/knowledge_items` |
| `get_knowledge_item` | `GET .../knowledge_items/:id` |
| `create_knowledge_item` | `POST .../knowledge_items` |
| `update_knowledge_item` | `PATCH .../knowledge_items/:id` |
| `delete_knowledge_item` | `DELETE .../knowledge_items/:id` |

```python
async def list_knowledge_items(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_knowledge_item(project_id: int | str, item_id: int | str) -> dict[str, Any]

async def create_knowledge_item(
    project_id: int | str,
    title: str,
    description: str,
    *,
    badge: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_knowledge_item(
    project_id: int | str,
    item_id: int | str,
    *,
    title: str | None = None,
    description: str | None = None,
    badge: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def delete_knowledge_item(project_id: int | str, item_id: int | str) -> None
```

---

## External Assets

| Function | Endpoint |
|---|---|
| `list_external_assets` | `GET /api/projects/:project_id/external_assets` |
| `get_external_asset` | `GET .../external_assets/:id` |
| `create_external_asset` | `POST .../external_assets` |
| `update_external_asset` | `PATCH .../external_assets/:id` |
| `delete_external_asset` | `DELETE .../external_assets/:id` |

```python
async def list_external_assets(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_external_asset(project_id: int | str, asset_id: int | str) -> dict[str, Any]

async def create_external_asset(
    project_id: int | str,
    title: str,
    url: str,
    *,
    doc_type: str | None = None,
    icon: str | None = None,
    source_type: str | None = None,
    meta_text: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_external_asset(
    project_id: int | str, asset_id: int | str, *, <same optional fields, plus title/url>
) -> dict[str, Any]

async def delete_external_asset(project_id: int | str, asset_id: int | str) -> None
```

`source_type` is `internal_file` or `external_url`.

---

## ADRs (Architectural Decision Records)

| Function | Endpoint |
|---|---|
| `list_adrs` | `GET /api/projects/:project_id/adrs` |
| `get_adr` | `GET .../adrs/:id` |
| `create_adr` | `POST .../adrs` |
| `update_adr` | `PATCH .../adrs/:id` |
| `delete_adr` | `DELETE .../adrs/:id` |

```python
async def list_adrs(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_adr(project_id: int | str, adr_id: int | str) -> dict[str, Any]

async def create_adr(
    project_id: int | str,
    identifier: str,
    title: str,
    *,
    decision_date: str | None = None,
    status: str | None = None,
    file_path: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_adr(
    project_id: int | str, adr_id: int | str, *, <same optional fields, plus identifier/title>
) -> dict[str, Any]

async def delete_adr(project_id: int | str, adr_id: int | str) -> None
```

`status` is one of `proposed`, `accepted`, `deprecated`, `superseded`.

---

## Knowledge Activities

| Function | Endpoint |
|---|---|
| `list_knowledge_activities` | `GET /api/projects/:project_id/knowledge_activities` |
| `get_knowledge_activity` | `GET .../knowledge_activities/:id` |
| `create_knowledge_activity` | `POST .../knowledge_activities` |
| `update_knowledge_activity` | `PATCH .../knowledge_activities/:id` |
| `delete_knowledge_activity` | `DELETE .../knowledge_activities/:id` |

```python
async def list_knowledge_activities(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_knowledge_activity(
    project_id: int | str, activity_id: int | str
) -> dict[str, Any]

async def create_knowledge_activity(
    project_id: int | str,
    actor_name: str,
    action_text: str,
    *,
    actor_color: str | None = None,
    target_path: str | None = None,
    target_url: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]

async def update_knowledge_activity(
    project_id: int | str, activity_id: int | str, *, <same optional fields, plus actor_name/action_text>
) -> dict[str, Any]

async def delete_knowledge_activity(project_id: int | str, activity_id: int | str) -> None
```

---

## Directory Items

Project file hierarchy backed by `storage/projects/:project_id/` on the server.

| Function | Endpoint |
|---|---|
| `list_directory_items` | `GET /api/projects/:project_id/directory_items` |
| `get_directory_item` | `GET .../directory_items/:id` |
| `create_directory_item` | `POST .../directory_items` |
| `update_directory_item` | `PATCH .../directory_items/:id` |
| `delete_directory_item` | `DELETE .../directory_items/:id` |

```python
async def list_directory_items(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_directory_item(project_id: int | str, item_id: int | str) -> dict[str, Any]

async def create_directory_item(
    project_id: int | str,
    *,
    name: str | None = None,
    item_type: str | None = None,
    file_path: str | None = None,
    parent_id: int | str | None = None,
    content: str | None = None,
    active: bool | None = None,
    position: int | None = None,
    file: FileUpload | None = None,
) -> dict[str, Any]

async def update_directory_item(
    project_id: int | str, item_id: int | str, *, <same fields as create>
) -> dict[str, Any]

async def delete_directory_item(project_id: int | str, item_id: int | str) -> None
```

`item_type` is `file` or `directory`. Supplying `file` writes it to
`storage/projects/:project_id/[file_path]`; deleting removes the file from disk.

---

## Obsidian Notes

Obsidian graph/note exports stored under `storage/projects/:project_id/`.

| Function | Endpoint |
|---|---|
| `list_obsidian_notes` | `GET /api/projects/:project_id/obsidian_notes` |
| `get_obsidian_note` | `GET .../obsidian_notes/:id` |
| `create_obsidian_note` | `POST .../obsidian_notes` |
| `update_obsidian_note` | `PATCH .../obsidian_notes/:id` |
| `delete_obsidian_note` | `DELETE .../obsidian_notes/:id` |

```python
async def list_obsidian_notes(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]

async def get_obsidian_note(project_id: int | str, note_id: int | str) -> dict[str, Any]

async def create_obsidian_note(
    project_id: int | str,
    *,
    title: str | None = None,
    tags: str | None = None,
    content: str | None = None,
    html_source_type: str | None = None,
    html_source_path: str | None = None,
    active: bool | None = None,
    position: int | None = None,
    file: FileUpload | None = None,
) -> dict[str, Any]

async def update_obsidian_note(
    project_id: int | str, note_id: int | str, *, <same fields as create>
) -> dict[str, Any]

async def delete_obsidian_note(project_id: int | str, note_id: int | str) -> None
```

`html_source_type` is `internal_file` or `external_url`. Supplying `file` writes it to
`storage/projects/:project_id/[html_source_path]`.

---

## Project Bottlenecks

| Function | Endpoint |
|---|---|
| `list_project_bottlenecks` | `GET /api/projects/:project_id/project_bottlenecks` |
| `get_project_bottleneck` | `GET .../project_bottlenecks/:id` |
| `create_project_bottleneck` | `POST .../project_bottlenecks` |
| `update_project_bottleneck` | `PATCH .../project_bottlenecks/:id` |
| `delete_project_bottleneck` | `DELETE .../project_bottlenecks/:id` |

```python
async def list_project_bottlenecks(
    project_id: int | str,
    *,
    created_at_gt: str | None = None,
    created_at_gte: str | None = None,
    created_at_lt: str | None = None,
    created_at_lte: str | None = None,
    from_: str | None = None,
    starts_at: str | None = None,
    start_date: str | None = None,
    to: str | None = None,
    ends_at: str | None = None,
    end_date: str | None = None,
    active: bool | None = None,
    severity: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> ProjectBottleneckList

async def get_project_bottleneck(
    project_id: int | str, bottleneck_id: int | str
) -> ProjectBottleneck

async def create_project_bottleneck(
    project_id: int | str,
    title: str,
    *,
    description: str | None = None,
    severity: str | None = None,
    position: int | None = None,
    resolved_at: str | None = None,
) -> ProjectBottleneck

async def update_project_bottleneck(
    project_id: int | str,
    bottleneck_id: int | str,
    *,
    title: str | None = None,
    description: str | None = None,
    severity: str | None = None,
    position: int | None = None,
    resolved_at: str | None = None,
    resolved: bool | None = None,
) -> ProjectBottleneck

async def delete_project_bottleneck(
    project_id: int | str, bottleneck_id: int | str
) -> None
```

---

## Project Todos

| Function | Endpoint |
|---|---|
| `list_project_todos` | `GET /api/projects/:project_id/project_todos` |
| `get_project_todo` | `GET .../project_todos/:id` |
| `create_project_todo` | `POST .../project_todos` |
| `update_project_todo` | `PATCH .../project_todos/:id` |
| `delete_project_todo` | `DELETE .../project_todos/:id` |

```python
async def list_project_todos(
    project_id: int | str,
    *,
    created_at_gt: str | None = None,
    created_at_gte: str | None = None,
    created_at_lt: str | None = None,
    created_at_lte: str | None = None,
    from_: str | None = None,
    starts_at: str | None = None,
    start_date: str | None = None,
    to: str | None = None,
    ends_at: str | None = None,
    end_date: str | None = None,
    completed: bool | None = None,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> ProjectTodoList

async def get_project_todo(
    project_id: int | str, todo_id: int | str
) -> ProjectTodo

async def create_project_todo(
    project_id: int | str,
    title: str,
    *,
    meta_text: str | None = None,
    completed: bool | None = None,
    completed_at: str | None = None,
    position: int | None = None,
) -> ProjectTodo

async def update_project_todo(
    project_id: int | str,
    todo_id: int | str,
    *,
    title: str | None = None,
    meta_text: str | None = None,
    completed: bool | None = None,
    completed_at: str | None = None,
    position: int | None = None,
) -> ProjectTodo

async def delete_project_todo(
    project_id: int | str, todo_id: int | str
) -> None
```

---

## Project Milestones

| Function | Endpoint |
|---|---|
| `list_project_milestones` | `GET /api/projects/:project_id/project_milestones` |
| `get_project_milestone` | `GET .../project_milestones/:id` |
| `create_project_milestone` | `POST .../project_milestones` |
| `update_project_milestone` | `PATCH .../project_milestones/:id` |
| `delete_project_milestone` | `DELETE .../project_milestones/:id` |

```python
async def list_project_milestones(
    project_id: int | str,
    *,
    created_at_gt: str | None = None,
    created_at_gte: str | None = None,
    created_at_lt: str | None = None,
    created_at_lte: str | None = None,
    from_: str | None = None,
    starts_at: str | None = None,
    start_date: str | None = None,
    to: str | None = None,
    ends_at: str | None = None,
    end_date: str | None = None,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> ProjectMilestoneList

async def get_project_milestone(
    project_id: int | str, milestone_id: int | str
) -> ProjectMilestone

async def create_project_milestone(
    project_id: int | str,
    title: str,
    *,
    description: str | None = None,
    icon: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> ProjectMilestone

async def update_project_milestone(
    project_id: int | str,
    milestone_id: int | str,
    *,
    title: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> ProjectMilestone

async def delete_project_milestone(
    project_id: int | str, milestone_id: int | str
) -> None
```

---

## Client Lifecycle

| Function | Purpose |
|---|---|
| `aclose_client` | Close the shared `AsyncClient` and release its connection pool |

```python
async def aclose_client() -> None
```

Safe to call more than once. Subsequent API calls recreate the client automatically, so this is
purely a shutdown/cleanup hook — for example from a FastAPI lifespan handler.

---

## Error Handling

```python
import httpx
from space import api

try:
    project = await api.get_project("acme")
except httpx.HTTPStatusError as exc:
    # 401 bad/missing OUTPUT_EVENTS_TOKEN, 404 not found, 422 validation, ...
    print(exc.response.status_code, exc.response.text)
except httpx.RequestError as exc:
    print("connection failure:", exc)
```

Common statuses: `401` (bad token), `400` (missing required param), `404` (not found),
`422` (validation error).

---

## Module Layout

| Module | Covers |
|---|---|
| [_client.py](../../space/api/_client.py) | Shared transport, auth headers, `aclose_client` |
| [projects.py](../../space/api/projects.py) | Projects |
| [rooms.py](../../space/api/rooms.py) | Rooms, threads, search |
| [messages.py](../../space/api/messages.py) | Messages (nested + flat), attachments |
| [actions.py](../../space/api/actions.py) | Typing indicators |
| [decisions.py](../../space/api/decisions.py) | Approval request resolution |
| [attention_items.py](../../space/api/attention_items.py) | Attention items |
| [company_status_periods.py](../../space/api/company_status_periods.py) | Company status periods |
| [company_status_items.py](../../space/api/company_status_items.py) | Company status items |
| [project_users.py](../../space/api/project_users.py) | Project members |
| [project_all_hands.py](../../space/api/project_all_hands.py) | All-hands takeaways, decisions, action items |
| [knowledge_items.py](../../space/api/knowledge_items.py) | Knowledge items |
| [external_assets.py](../../space/api/external_assets.py) | External assets |
| [adrs.py](../../space/api/adrs.py) | ADRs |
| [knowledge_activities.py](../../space/api/knowledge_activities.py) | Knowledge activities |
| [directory_items.py](../../space/api/directory_items.py) | Directory items |
| [obsidian_notes.py](../../space/api/obsidian_notes.py) | Obsidian notes |
| [project_bottlenecks.py](../../space/api/project_bottlenecks.py) | Project bottlenecks |
| [project_todos.py](../../space/api/project_todos.py) | Project todos |
| [project_milestones.py](../../space/api/project_milestones.py) | Project milestones |
