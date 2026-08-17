#!/usr/bin/env python3
"""Long-poll daemon that prints arrived room messages from ROOM_BASE_URL/mcp."""

import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


_running = True
_state: dict[str, object] = {}


def _load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE pairs from .env when variables are not already exported."""
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as exc:
        print(f"[dotenv] failed to read {path}: {exc}", file=sys.stderr, flush=True)


_load_dotenv()

ROOM_BASE_URL = os.environ.get("ROOM_BASE_URL", "http://localhost:3000").rstrip("/")
MCP_URL = f"{ROOM_BASE_URL}/mcp"
PROJECT_PATH = os.environ.get("PROJECT_PATH", os.getcwd())
AGENT_NAME = os.environ.get("AGENT_NAME", "Observer")
PROGRAM = os.environ.get("PROGRAM", "Room MCP Poll Daemon")
MODEL = (os.environ.get("AGENT_MODEL") or os.environ.get("MODEL") or "deepseek-v4-flash").strip()
POLL_TIMEOUT = min(max(int(os.environ.get("POLL_TIMEOUT", "30")), 1), 60)
RETRY_SLEEP_SECONDS = max(float(os.environ.get("RETRY_SLEEP_SECONDS", "5")), 0.5)
ROOM_SYNC_INTERVAL = max(float(os.environ.get("ROOM_SYNC_INTERVAL", "60")), 5.0)
JOIN_DIRECT_ROOMS = os.environ.get("JOIN_DIRECT_ROOMS", "0") == "1"
REGISTER_WITH_PROJECT_PATH = os.environ.get("REGISTER_WITH_PROJECT_PATH", "0") == "1"
ROOM_LIST_TYPES = [
    value.strip() for value in os.environ.get("ROOM_LIST_TYPES", "all,joined,public,project").split(",") if value.strip()
]
ROOM_IDS = [
    value.strip() for value in os.environ.get("ROOM_IDS", "").split(",") if value.strip()
]
LIST_ROOMS_ONLY = os.environ.get("LIST_ROOMS_ONLY", "0") == "1"


def _log_error(message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)


def _rpc_call(method: str, arguments: dict, auth: bool = True) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 10**9,
        "method": "tools/call",
        "params": {"name": method, "arguments": arguments},
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    if auth and _state.get("api_token"):
        headers["Authorization"] = f"Bearer {str(_state['api_token'])}"
    if auth and _state.get("session_id"):
        headers["Mcp-Session-Id"] = str(_state["session_id"])

    request = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=POLL_TIMEOUT + 10) as response:
            response_json = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:400]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error: {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Transport error: {exc}") from exc

    if "error" in response_json:
        error_obj = response_json.get("error") or {}
        raise RuntimeError(f"JSON-RPC error: {error_obj}")

    result = response_json.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"Invalid MCP response: missing result object ({response_json})")

    if result.get("isError"):
        content = result.get("content") or []
        details = content[0].get("text", "unknown MCP error") if content else "unknown MCP error"
        raise RuntimeError(details)

    # Standard MCP tool result shape: content[0].text contains JSON payload.
    content = result.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and "text" in first:
            text_payload = first.get("text", "")
            try:
                return json.loads(text_payload)
            except json.JSONDecodeError:
                # Some servers return plain text for non-JSON tool payloads.
                return {"text": str(text_payload)}

    # Alternate MCP shape supported by some implementations.
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured

    # Fallback: if result already looks like the tool payload, return it.
    direct_payload = {k: v for k, v in result.items() if k not in {"content", "isError", "structuredContent"}}
    if direct_payload:
        return direct_payload

    raise RuntimeError(f"Invalid MCP response shape for method '{method}': {result}")


def _register_agent() -> None:
    base_args = {
        "program": PROGRAM,
        "name": AGENT_NAME,
        "task_description": "Listen for new room messages and print them",
    }
    can_include_project_path = bool(PROJECT_PATH)
    can_include_model = bool(MODEL)

    # Try both project-scoped and non-project-scoped registrations, because
    # different servers enforce different required argument sets.
    preferred_project = REGISTER_WITH_PROJECT_PATH
    include_project_options = [preferred_project, not preferred_project] if can_include_project_path else [False]
    include_model_options = [True, False] if can_include_model else [False]

    attempt_args: list[dict] = []
    for include_project in include_project_options:
        for include_model in include_model_options:
            args = dict(base_args)
            if include_model and MODEL:
                args["model"] = MODEL
            if include_project and PROJECT_PATH:
                args["project_path"] = PROJECT_PATH
            attempt_args.append(args)

    # Deduplicate attempts while preserving order.
    deduped_attempts: list[dict] = []
    seen = set()
    for args in attempt_args:
        key = tuple(sorted(args.items()))
        if key in seen:
            continue
        seen.add(key)
        deduped_attempts.append(args)

    result = None
    last_error = None
    for args in deduped_attempts:
        try:
            result = _rpc_call("register_agent", args, auth=False)
            break
        except Exception as exc:
            last_error = exc
            _log_error(f"register_agent failed with args keys={sorted(args.keys())}: {exc}")

    if result is None:
        raise RuntimeError(f"register_agent failed after retries: {last_error}")

    credentials = result.get("credentials") or {}
    api_token = credentials.get("api_token")
    session_id = credentials.get("session_id")

    if not api_token or not session_id:
        raise RuntimeError("register_agent did not return credentials")

    _state["api_token"] = api_token
    _state["session_id"] = session_id


def _poll_once(since: str) -> tuple[list[dict], str]:
    poll_args: dict = {
        "since": since,
        "timeout_seconds": POLL_TIMEOUT,
    }
    if _state.get("room_ids"):
        poll_args["room_ids"] = _state["room_ids"]

    data = _rpc_call("poll_messages", poll_args)

    messages = data.get("messages", [])
    polled_until = data.get("polled_until")
    if not isinstance(messages, list) or not polled_until:
        raise RuntimeError("poll_messages returned invalid payload")

    return messages, polled_until


def _heartbeat() -> None:
    _rpc_call("heartbeat", {"renew_reservations": True})


def _discover_rooms() -> list[dict]:
    """Collect visible rooms across configured list types and deduplicate by id."""
    discovered: dict[int, dict] = {}
    discovered_per_type: dict[str, int] = {}
    for room_type in ROOM_LIST_TYPES:
        try:
            rooms_data = _rpc_call(
                "list_rooms",
                {
                    "type": room_type,
                    "include_archived": True,
                },
            )
        except Exception as exc:
            _log_error(f"list_rooms failed for type={room_type}: {exc}")
            continue

        rooms = rooms_data.get("rooms", [])
        if not isinstance(rooms, list):
            continue
        discovered_per_type[room_type] = len(rooms)

        for room in rooms:
            if not isinstance(room, dict):
                continue
            room_id = room.get("id")
            if isinstance(room_id, int):
                discovered[room_id] = room

    if discovered_per_type:
        counts = ", ".join(f"{room_type}:{count}" for room_type, count in discovered_per_type.items())
        _log_error(f"room discovery counts ({counts}), unique={len(discovered)}")

    return list(discovered.values())


def _log_visible_rooms(rooms: list[dict]) -> None:
    """Print a compact room list so users can inspect visibility and ids."""
    if not rooms:
        _log_error("Visible rooms: none")
        return

    sorted_rooms = sorted(rooms, key=lambda room: int(room.get("id", 0)))
    _log_error(f"Visible rooms ({len(sorted_rooms)}):")
    for room in sorted_rooms:
        room_id = room.get("id")
        name = room.get("name") or "(no-name)"
        room_type = room.get("type") or "unknown"
        joined = bool(room.get("joined"))
        archived = bool(room.get("archived"))
        _log_error(
            f"  id={room_id} name={name} type={room_type} joined={joined} archived={archived}"
        )


def _sync_new_rooms() -> int:
    """Join newly created rooms so polling can include them automatically."""
    rooms = _discover_rooms()
    if not rooms:
        _log_error("Room discovery returned 0 rooms")
        return 0

    joined_count = 0
    for room in rooms:
        if not isinstance(room, dict):
            continue
        if room.get("archived"):
            continue
        if room.get("type") == "Rooms::Direct" and not JOIN_DIRECT_ROOMS:
            continue
        if room.get("joined"):
            continue

        room_id = room.get("id")
        if not room_id:
            continue

        _rpc_call("join_room", {"room_id": room_id})
        joined_count += 1

    if joined_count > 0:
        _log_error(f"Joined {joined_count} new room(s)")
    elif len(rooms) <= 1:
        _log_error(
            "Only one visible room discovered. Set REGISTER_WITH_PROJECT_PATH=0 and/or provide ROOM_IDS=<id1,id2> for explicit polling."
        )

    return joined_count


def _apply_explicit_room_ids() -> None:
    """Use explicit room ids when server-side discovery visibility is limited."""
    if not ROOM_IDS:
        return

    valid_room_ids: list[str] = []
    for raw_room_id in ROOM_IDS:
        try:
            valid_room_ids.append(str(int(raw_room_id)))
        except ValueError:
            _log_error(f"Ignoring invalid ROOM_IDS value: {raw_room_id}")

    if not valid_room_ids:
        _log_error("ROOM_IDS provided but no valid numeric ids found")
        return

    for room_id in valid_room_ids:
        try:
            _rpc_call("join_room", {"room_id": int(room_id)})
        except Exception as exc:
            _log_error(f"join_room failed for room_id={room_id}: {exc}")

    _state["room_ids"] = valid_room_ids
    _log_error(f"Using explicit ROOM_IDS filter: {valid_room_ids}")


def _print_arrived_messages(messages: list[dict]) -> None:
    for message in messages:
        body = (message.get("body") or "").strip()
        if body:
            print(body, flush=True)


def _shutdown(signum=None, frame=None) -> None:
    del frame
    global _running
    _running = False
    if signum is not None:
        _log_error(f"Signal {signum} received, shutting down")

    try:
        if _state.get("api_token") and _state.get("session_id"):
            _rpc_call("update_agent_status", {"status": "offline"})
    except Exception as exc:
        _log_error(f"Failed to set offline status: {exc}")


def main() -> None:
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    _register_agent()
    rooms = _discover_rooms()
    _log_visible_rooms(rooms)
    if LIST_ROOMS_ONLY:
        return

    try:
        _sync_new_rooms()
    except Exception as exc:
        _log_error(f"Initial room sync error: {exc}")
    _apply_explicit_room_ids()

    since = datetime.now(timezone.utc).isoformat()
    next_room_sync_at = time.monotonic() + ROOM_SYNC_INTERVAL

    while _running:
        try:
            messages, since = _poll_once(since)
            _print_arrived_messages(messages)
            _heartbeat()

            if time.monotonic() >= next_room_sync_at:
                try:
                    _sync_new_rooms()
                except Exception as exc:
                    _log_error(f"Room sync error: {exc}")
                next_room_sync_at = time.monotonic() + ROOM_SYNC_INTERVAL
        except KeyboardInterrupt:
            _shutdown()
        except Exception as exc:
            _log_error(f"Poll cycle error: {exc}")
            time.sleep(RETRY_SLEEP_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _log_error(f"Fatal error: {exc}")
        sys.exit(1)
