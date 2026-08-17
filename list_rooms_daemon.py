#!/usr/bin/env python3
"""Print visible MCP rooms to console."""

import json
import os
import sys
import time
import urllib.error
import urllib.request


_state: dict[str, str] = {}


def _load_dotenv(path: str = ".env") -> None:
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
        print(f"Failed to read .env: {exc}", file=sys.stderr, flush=True)


_load_dotenv()

ROOM_BASE_URL = os.environ.get("ROOM_BASE_URL", "http://localhost:3000").rstrip("/")
MCP_URL = f"{ROOM_BASE_URL}/mcp"
PROJECT_PATH = os.environ.get("PROJECT_PATH", os.getcwd())
AGENT_NAME = os.environ.get("AGENT_NAME", "Room Lister")
PROGRAM = os.environ.get("PROGRAM", "Room List Utility")
MODEL = (os.environ.get("AGENT_MODEL") or os.environ.get("MODEL") or "deepseek-v4-flash").strip()
REGISTER_WITH_PROJECT_PATH = os.environ.get("REGISTER_WITH_PROJECT_PATH", "1") == "1"
ROOM_LIST_TYPES = [
    value.strip()
    for value in os.environ.get("ROOM_LIST_TYPES", "all,joined,public,project").split(",")
    if value.strip()
]


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
        headers["Authorization"] = f"Bearer {_state['api_token']}"
    if auth and _state.get("session_id"):
        headers["Mcp-Session-Id"] = _state["session_id"]

    request = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            response_json = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:400]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error: {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Transport error: {exc}") from exc

    if "error" in response_json:
        raise RuntimeError(f"JSON-RPC error: {response_json.get('error')}")

    result = response_json.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"Invalid MCP response: {response_json}")

    if result.get("isError"):
        content = result.get("content") or []
        text = content[0].get("text", "unknown MCP error") if content else "unknown MCP error"
        raise RuntimeError(text)

    content = result.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and "text" in first:
            text = first.get("text", "")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": str(text)}

    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured

    direct_payload = {k: v for k, v in result.items() if k not in {"content", "isError", "structuredContent"}}
    if direct_payload:
        return direct_payload

    raise RuntimeError(f"Invalid MCP result shape for {method}: {result}")


def _register_agent() -> None:
    base_args = {
        "program": PROGRAM,
        "name": AGENT_NAME,
        "task_description": "List visible rooms",
    }
    if MODEL:
        base_args["model"] = MODEL

    attempt_args: list[dict] = []
    include_project_options = [REGISTER_WITH_PROJECT_PATH, not REGISTER_WITH_PROJECT_PATH]

    for include_project in include_project_options:
        args = dict(base_args)
        if include_project and PROJECT_PATH:
            args["project_path"] = PROJECT_PATH
        attempt_args.append(args)

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

    if result is None:
        raise RuntimeError(f"register_agent failed: {last_error}")

    credentials = result.get("credentials") or {}
    api_token = credentials.get("api_token")
    session_id = credentials.get("session_id")

    if not api_token or not session_id:
        raise RuntimeError("register_agent did not return credentials")

    _state["api_token"] = api_token
    _state["session_id"] = session_id


def _print_rooms() -> None:
    all_rooms: dict[int, dict] = {}

    for room_type in ROOM_LIST_TYPES:
        data = _rpc_call("list_rooms", {"type": room_type, "include_archived": True})
        rooms = data.get("rooms", [])
        if not isinstance(rooms, list):
            print(f"type={room_type}: invalid payload")
            continue

        print(f"type={room_type}: count={len(rooms)}")
        for room in rooms:
            if not isinstance(room, dict):
                continue
            room_id = room.get("id")
            name = room.get("name")
            room_kind = room.get("type")
            joined = room.get("joined")
            archived = room.get("archived")
            print(f"  id={room_id} name={name} type={room_kind} joined={joined} archived={archived}")
            if isinstance(room_id, int):
                all_rooms[room_id] = room

    print(f"unique_rooms={len(all_rooms)}")


def main() -> None:
    _register_agent()
    _print_rooms()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        sys.exit(1)
