#!/usr/bin/env python3
"""
Bonfire -> Hermes answer bridge daemon.

Watches Bonfire rooms. When a question arrives from a user, it asks Hermes
(`hermes chat -q`) to answer it and posts the answer back into the room as
the daemon's agent identity.

By default it listens to ALL rooms the agent has joined (poll_messages
without room_ids polls every joined room). With JOIN_ALL_ROOMS=1 (default)
it also joins every non-direct room at startup, so you never need to name
rooms. Set ROOM_IDS to restrict to a specific subset.

Plumbing (poll loop, registration, heartbeat, state file) is the same as
agent_daemon.py; the handler differs: it delegates to Hermes instead of
echoing.

Usage:
    ./hermes_bridge_daemon.py                 # join all rooms, watch all
    ROOM_IDS=4 ./hermes_bridge_daemon.py      # watch only room 4
    JOIN_ALL_ROOMS=0 ./hermes_bridge_daemon.py # watch only already-joined rooms
    AGENT_NAME="Hermes Bridge" ./hermes_bridge_daemon.py

Environment variables (all optional):
    BONFIRE_URL     MCP endpoint           (default http://localhost:3000/mcp)
    PROJECT_PATH    project root           (default /home/siavash/Documents/codes/Pavel/chat)
    AGENT_NAME      daemon agent identity  (default "Hermes Bridge")
    PROGRAM         agent program label    (default "Hermes Bridge Daemon")
    MODEL           agent model label      (default "deepseek-v4-flash")
    ROOM_IDS        comma-separated rooms to watch; EMPTY = all joined rooms
    JOIN_ALL_ROOMS  "1" (default) join every non-direct room at startup;
                    "0" only use rooms the agent already belongs to
    JOIN_DIRECT     "1" also join direct/private rooms; "0" (default) skip them
    POLL_TIMEOUT    long-poll seconds      (default 30, max 60)
    HERMES_TIMEOUT  seconds per question   (default 240)
    QUESTION_ONLY   "1" (default) answer only messages containing '?';
                    "0" answer every user message
    REPORT_ERRORS   "1" (default) post a short notice when Hermes fails
    STATE_FILE      credential cache       (default ./hermes_bridge_state.json)
"""

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BONFIRE_URL = os.environ.get("BONFIRE_URL", "http://localhost:3000/mcp")
PROJECT_PATH = os.environ.get(
    "PROJECT_PATH", "..center(length, character)"
)
AGENT_NAME = os.environ.get("AGENT_NAME", "Hermes Bridge")
PROGRAM = os.environ.get("PROGRAM", "Hermes Bridge Daemon")
MODEL = os.environ.get("MODEL", "deepseek-v4-flash")
ROOM_IDS = [r.strip() for r in os.environ.get("ROOM_IDS", "").split(",") if r.strip()]
JOIN_ALL_ROOMS = os.environ.get("JOIN_ALL_ROOMS", "1") == "1"
JOIN_DIRECT = os.environ.get("JOIN_DIRECT", "0") == "1"
POLL_TIMEOUT = min(int(os.environ.get("POLL_TIMEOUT", "30")), 60)
HERMES_TIMEOUT = int(os.environ.get("HERMES_TIMEOUT", "240"))
QUESTION_ONLY = os.environ.get("QUESTION_ONLY", "1") == "1"
REPORT_ERRORS = os.environ.get("REPORT_ERRORS", "1") == "1"
STATE_FILE = os.environ.get("STATE_FILE", "./hermes_bridge_state.json")

_state = {}
_running = True


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def rpc(method: str, params: dict, auth: bool = True) -> dict:
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
    return json.loads(result["content"][0]["text"])


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
        except Exception:
            pass
    return False


def register() -> None:
    """Idempotently register/resume the agent identity (register_agent)."""
    data = rpc("register_agent", {
        "project_path": PROJECT_PATH, "program": PROGRAM,
        "model": MODEL, "name": AGENT_NAME,
        "task_description": f"Watching rooms {ROOM_IDS or 'all rooms'}; "
                            f"answers questions via Hermes",
    }, auth=False)
    _state.update({
        "api_token": data["credentials"]["api_token"],
        "session_id": data["credentials"]["session_id"],
        "agent_name": data["agent_name"],
        "agent_id": data["agent_id"],
        # Empty room_ids = "all joined rooms" (server-side default).
        "room_ids": ROOM_IDS,
        "project_room_id": data["room_id"],
    })
    save_state()
    log(f"agent '{data['agent_name']}' (id {data['agent_id']}) "
        f"{'reconnected' if data.get('reconnected') else 'registered'} in room {data['room_id']}")


def join_all_rooms() -> list:
    """Join every room the agent can see (skipping direct/private rooms unless
    JOIN_DIRECT=1), so a bare run watches the whole server."""
    data = rpc("list_rooms", {"type": "all", "include_archived": False})
    rooms = data.get("rooms", [])
    joined = []
    for room in rooms:
        rid = room["id"]
        if room.get("archived"):
            continue
        if room.get("type") == "Rooms::Direct" and not JOIN_DIRECT:
            log(f"skipping direct room {rid} ({room.get('name')})")
            continue
        if not room.get("joined"):
            rpc("join_room", {"room_id": rid})
            log(f"joined room {rid} ({room.get('name')})")
        joined.append(rid)
    _state["room_ids"] = joined
    save_state()
    log(f"watching {len(joined)} rooms: {sorted(joined)}")
    return joined


def poll_once(since: str) -> tuple[list, str]:
    args = {"since": since, "timeout_seconds": POLL_TIMEOUT}
    # Omit room_ids entirely for "all joined rooms" (server-side default).
    if _state.get("room_ids"):
        args["room_ids"] = _state["room_ids"]
    data = rpc("poll_messages", args)
    return data.get("messages", []), data["polled_until"]


def heartbeat() -> None:
    rpc("heartbeat", {"renew_reservations": True})


def ask_hermes(question: str) -> str:
    """Run Hermes one-shot and return its answer (session_id line stripped).

    hermes chat -q prints 'session_id: <id>' on the first line in quiet mode,
    then the final response. Only that response gets posted back.
    """
    cmd = ["hermes", "chat", "-q", question, "-Q"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=HERMES_TIMEOUT)
    out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        raise RuntimeError(f"hermes exited {proc.returncode}: {(proc.stderr or '')[-300:]}")
    # Drop the leading 'session_id: ...' line if present
    lines = out.splitlines()
    if lines and lines[0].startswith("session_id:"):
        lines = lines[1:]
    answer = "\n".join(lines).strip()
    if not answer:
        raise RuntimeError("hermes returned an empty response")
    return answer


def is_question(msg: dict) -> bool:
    if QUESTION_ONLY:
        return "?" in (msg.get("body") or "")
    return True


def handle_message(msg: dict) -> None:
    """Delegate one room message to Hermes and post the answer back."""
    room_id = msg.get("room_id")
    creator = msg.get("creator", {})
    if creator.get("type") == "Agent":
        log(f"skipping agent message #{msg.get('id')} from {creator.get('name')}")
        return
    if msg.get("system"):
        log(f"skipping system message #{msg.get('id')}")
        return

    body = (msg.get("body") or "").strip()
    if not body:
        return
    if not is_question(msg):
        log(f"skipping non-question #{msg.get('id')} from {creator.get('name')}")
        return

    log(f"question #{msg.get('id')} from {creator.get('name')}: {body[:80]}")
    question = (f"Someone in a chat room ({creator.get('name', 'a user')}) asks: {body}\n"
                f"Answer concisely and directly.")
    try:
        answer = ask_hermes(question)
        log(f"hermes answered #{msg.get('id')} ({len(answer)} chars)")
        rpc("send_message", {"room_id": room_id, "body": answer})
        log(f"posted answer to #{msg.get('id')}")
    except Exception as e:
        log(f"failed to answer #{msg.get('id')}: {e}")
        if REPORT_ERRORS:
            try:
                rpc("send_message", {
                    "room_id": room_id,
                    "body": f"⚠️ Hermes could not answer this one: {str(e)[:200]}",
                })
            except Exception:
                pass


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

    # Explicit ROOM_IDS wins. Otherwise clear any stale room list from a
    # previous run so a bare run always means "all rooms".
    if ROOM_IDS:
        _state["room_ids"] = ROOM_IDS
    else:
        _state["room_ids"] = []

    # Bare run = watch everything: join all non-direct rooms, then poll all.
    if not _state.get("room_ids") and JOIN_ALL_ROOMS:
        join_all_rooms()
    elif not _state.get("room_ids"):
        log("watching all already-joined rooms (JOIN_ALL_ROOMS=0)")

    since = datetime.now(timezone.utc).isoformat()
    log(f"watching rooms {_state['room_ids'] or 'ALL JOINED'} "
        f"(question_only={QUESTION_ONLY}, hermes_timeout={HERMES_TIMEOUT}s), since={since}")

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
    main()
