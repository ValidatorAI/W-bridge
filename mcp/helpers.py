import re
from difflib import SequenceMatcher
from typing import Any, Iterable

from space.api.project_users import list_project_users
from space.api.projects import list_projects
from space.api.rooms import list_rooms, search_rooms


def _normalize_name(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, (int, float)):
        text = str(value)
    elif isinstance(value, dict):
        for key in ("name", "display_name", "username", "email_address", "slug", "profile_name"):
            if key in value and value[key] is not None:
                return _normalize_name(value[key])
        text = str(value)
    else:
        text = str(value)

    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _score_fuzzy_match(query: str, candidate: str) -> float:
    q = _normalize_name(query)
    c = _normalize_name(candidate)

    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    if q in c or c in q:
        return 0.9

    score = SequenceMatcher(None, q, c).ratio()
    q_tokens = set(q.split())
    c_tokens = set(c.split())
    overlap = (
        (len(q_tokens & c_tokens) / max(len(q_tokens | c_tokens), 1))
        if (q_tokens or c_tokens)
        else 0.0
    )
    return max(score, overlap)


def _pick_best_match(query: str, records: Iterable[Any], key_getter) -> Any | None:
    if query is None:
        return None

    query_text = str(query).strip()
    if not query_text:
        return None

    best_record = None
    best_score = 0.0

    for record in records:
        candidate_value = key_getter(record)
        if candidate_value is None:
            continue
        score = _score_fuzzy_match(query_text, candidate_value)
        if score > best_score:
            best_score = score
            best_record = record

    if best_record is None or best_score < 0.4:
        return None

    return best_record


async def username_fuzzy_match(project_id: int | str, username: str) -> dict[str, Any] | None:
    """Return the single best-matching project user by name, display name, or email."""
    payload = await list_project_users(project_id)
    records = payload.get("project_users", []) if isinstance(payload, dict) else payload or []

    def get_name(user: Any) -> str:
        if isinstance(user, dict):
            return (
                user.get("name")
                or user.get("display_name")
                or user.get("email_address")
                or ""
            )
        return (
            getattr(user, "name", "")
            or getattr(user, "display_name", "")
            or getattr(user, "email_address", "")
            or ""
        )

    return _pick_best_match(username, records, get_name)


async def project_name_fuzzy_match(project_name: str) -> dict[str, Any] | None:
    """Return the single best-matching project by name or slug."""
    projects = await list_projects()

    def get_name(project: Any) -> str:
        if isinstance(project, dict):
            return project.get("name") or project.get("slug") or ""
        return getattr(project, "name", "") or getattr(project, "slug", "") or ""

    return _pick_best_match(project_name, projects, get_name)


async def room_name_fuzzy(project_id: int | str, room_name: str) -> dict[str, Any] | None:
    """Return the single best-matching room within a project by name."""
    try:
        rooms = await search_rooms(project_id, room_name)
    except Exception:
        rooms = []

    if not rooms:
        rooms = await list_rooms(project_id)

    def get_name(room: Any) -> str:
        if isinstance(room, dict):
            return room.get("name") or ""
        return getattr(room, "name", "") or ""

    return _pick_best_match(room_name, rooms, get_name)


async def bot_name_fuzzy_match(project_id: int | str, bot_name: str) -> dict[str, Any] | None:
    """Return the single best-matching bot (role == 2) from project users."""
    payload = await list_project_users(project_id)
    records = payload.get("project_users", []) if isinstance(payload, dict) else payload or []
    bots = [
        record
        for record in records
        if (record.get("role") if isinstance(record, dict) else getattr(record, "role", None)) == 2
    ]

    def get_name(bot: Any) -> str:
        if isinstance(bot, dict):
            return bot.get("name") or bot.get("display_name") or ""
        return getattr(bot, "name", "") or getattr(bot, "display_name", "") or ""

    return _pick_best_match(bot_name, bots, get_name)


# Convenience aliases matching the requested naming variants.
project_name_fuzzy = project_name_fuzzy_match
room_name_fuzzy_match = room_name_fuzzy
bot_name_fuzzy = bot_name_fuzzy_match
username_fuzzy = username_fuzzy_match
