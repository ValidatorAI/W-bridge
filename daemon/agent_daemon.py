#!/usr/bin/env python3
"""
Bonfire long-poll agent daemon (example).

A self-contained background daemon that keeps an MCP agent identity alive:
registers/resumes via macro_start_session, long-polls poll_messages in a
loop, heartbeats, and replies to room messages (demo handler: echo).

No dependencies beyond the Python standard library.

Usage:
    ./agent_daemon.py                      # register a fresh auto-named agent
    AGENT_NAME="Echo Daemon" ./agent_daemon.py   # resume/create by name
    ./agent_daemon.py --once               # single poll cycle, then exit

Environment variables (all optional):
    BONFIRE_URL    MCP endpoint           (default http://localhost:3000/mcp)
    PROJECT_PATH   project root           (default /home/siavash/Documents/codes/Pavel/chat)
    AGENT_NAME     agent identity to resume/create
    PROGRAM        agent program label    (default "Hermes Agent Daemon")
    MODEL          model identifier       (default "deepseek-v4-flash")
    ROOM_IDS       comma-separated room ids to poll (default: all joined)
    POLL_TIMEOUT   long-poll seconds      (default 30, max 60)
    STATE_FILE     credential cache       (default ./agent_daemon_state.json)
"""

import json
import os
import signal
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BONFIRE_URL = os.environ.get("BONFIRE_URL", "http://localhost:3000/mcp")
PROJECT_PATH = os.environ.get(
    "PROJECT_PATH", "/home/siavash/Documents/codes/Pavel/chat"
)
AGENT_NAME = os.environ.get("AGENT_NAME", "")
PROGRAM = os.environ.get("PROGRAM", "Hermes Agent Daemon")
MODEL = os.environ.get("MODEL", "deepseek-v4-flash")
ROOM_IDS = [r.strip() for r in os.environ.get("ROOM_IDS", "").split(",") if r.strip()]
POLL_TIMEOUT = min(int(os.environ.get("POLL_TIMEOUT", "30")), 60)
STATE_FILE = os.environ.get("STATE_FILE", "./agent_daemon_state.json")

_state = {}          # {api_token, session_id, agent_name, agent_id, room_ids}
_running = True


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def rpc(method: str, params: dict, auth: bool = True) -> dict:
    """Call a Bonfire MCP tool over JSON-RPC (Streamable HTTP)."""
    payload = json.dumps({"jsonrpc": "2.0", "id": int(time.time() * 1000) % 10**9,
                          "method": "tools/call",
                          "params": {"name": method, "arguments": params}}).encode()
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if auth and _state.get("api_token"):
        headers["Authorization"] = f"Bearer {_state['api_token']}"
    if auth and _state.get("session_id"):
        headers["Mcp-Session-Id"] = _state["session_id"]

    req = urllib.request.Request(BONFIRE_URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=POLL_TIMEOUT + 10) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        raise RuntimeError(f"transport error: {e}")

    result = body.get("result") or {}
    if result.get("isError"):
        raise RuntimeError(f"MCP error: {result.get('content', [{}])[0].get('text', '')[:300]}")
    text = result["content"][0]["text"]
    return json.loads(text)  # tool payload is a JSON string inside content[0].text


def save_state() -> None:
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(_state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def load_state() -> bool:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                _state.update(json.load(f))
            return bool(_state.get("api_token"))
        except Exception as e:
            log(f"state file unreadable ({e}), registering fresh")
    return False


def register() -> None:
    """Register or resume the agent identity and join the project room.

    register_agent is idempotent by name (creates if missing, reconnects if
    present). macro_start_session is used only for auto-generated names.
    """
    task = f"Long-poll daemon watching rooms: {ROOM_IDS or 'all joined'}"
    name = AGENT_NAME or _state.get("agent_name")

    if name:
        data = rpc("register_agent", {
            "project_path": PROJECT_PATH, "program": PROGRAM,
            "model": MODEL, "name": name, "task_description": task,
        }, auth=False)
        _state.update({
            "api_token": data["credentials"]["api_token"],
            "session_id": data["credentials"]["session_id"],
            "agent_name": data["agent_name"],
            "agent_id": data["agent_id"],
            "room_ids": ROOM_IDS or [data["room_id"]],
        })
        save_state()
        log(f"agent '{data['agent_name']}' (id {data['agent_id']}) "
            f"{'reconnected' if data.get('reconnected') else 'registered'} in room "
            f"{data['room_id']}")
    else:
        data = rpc("macro_start_session", {
            "project_path": PROJECT_PATH, "program": PROGRAM,
            "model": MODEL, "task_description": task,
        }, auth=False)
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"registration failed: {data.get('message', data)}")
        _state.update({
            "api_token": data["credentials"]["api_token"],
            "session_id": data["credentials"]["session_id"],
            "agent_name": data["agent"]["name"],
            "agent_id": data["agent"]["id"],
            "room_ids": ROOM_IDS or [data["room"]["id"]],
        })
        save_state()
        log(f"agent '{_state['agent_name']}' (id {_state['agent_id']}) "
            f"{'reconnected' if data.get('reconnected') else 'registered'} in room "
            f"{data['room']['id']} ({data['room']['name']})")


def poll_once(since: str) -> tuple[list, str]:
    """One long-poll cycle. Returns (messages, polled_until)."""
    args = {"since": since, "timeout_seconds": POLL_TIMEOUT}
    if _state.get("room_ids"):
        args["room_ids"] = _state["room_ids"]
    data = rpc("poll_messages", args)
    return data.get("messages", []), data["polled_until"]


def heartbeat() -> None:
    rpc("heartbeat", {"renew_reservations": True})


def handle_message(msg: dict) -> None:
    """Demo handler: echo the message back into its room."""
    room_id = msg.get("room_id")
    creator = msg.get("creator", {}).get("name", "someone")
    body = (msg.get("body") or "").strip()
    log(f"message #{msg.get('id')} from {creator}: {body[:80]}")
    reply = f"Echo from {_state['agent_name']} (daemon): \"{body}\""
    rpc("send_message", {"room_id": room_id, "body": reply})
    log(f"replied to #{msg.get('id')}")


def shutdown(signum=None, frame=None) -> None:
    global _running
    _running = False
    log(f"signal {signum} received, going offline")
    try:
        rpc("update_agent_status", {"status": "offline"})
    except Exception as e:
        log(f"could not set offline status: {e}")


def main() -> None:
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    if not load_state():
        register()
    else:
        log(f"resuming from state file as '{_state['agent_name']}'")

    # Cursor contract: polled_until from each poll becomes the next `since`.
    since = datetime.now(timezone.utc).isoformat()
    log(f"starting long-poll loop (timeout {POLL_TIMEOUT}s), since={since}")

    while _running:
        try:
            messages, since = poll_once(since)
            for m in messages:
                handle_message(m)
            heartbeat()
        except KeyboardInterrupt:
            shutdown()
        except Exception as e:
            log(f"poll cycle error: {e}; retrying in 5s")
            time.sleep(5)

    log("daemon stopped")


if __name__ == "__main__":
    if "--once" in sys.argv:
        register()
        msgs, since = poll_once(datetime.now(timezone.utc).isoformat())
        for m in msgs:
            handle_message(m)
        shutdown()
    else:
        main()
